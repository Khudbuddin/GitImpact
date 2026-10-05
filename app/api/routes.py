import os
from fastapi import APIRouter
from pydantic import BaseModel

from app.ingestion.cloner import clone_repository
from app.parsing.repo_scanner import scan_repository
from app.graph.builder import (
    build_dependency_graph,
    get_file_level_view,
    get_graph_summary,
    generate_mermaid_diagram
)
from app.agents.orchestrator import route_and_execute_query
from app.database.db import save_repo_metadata

router = APIRouter()

# In-memory store: repo_name -> {graph, repo_data, metadata}
REPO_STORE = {}


class CloneRequest(BaseModel):
    repo_url: str


class ChatRequest(BaseModel):
    repo_name: str | None = None
    message: str
    file_path: str | None = None


class QuestionRequest(BaseModel):
    repo_name: str
    file_path: str
    function_name: str
    question: str


@router.get("/")
def read_root():
    return {"message": "GitImpact backend is running"}


@router.get("/health")
def health_check():
    return {"status": "GitImpact API is alive"}


@router.post("/clone")
def clone_and_analyze(request: CloneRequest):
    """
    Clones the given GitHub repo, parses AST for supported files,
    extracts directory structures, tech stack, README documentation,
    and constructs the dependency graph.
    """
    try:
        clone_result = clone_repository(request.repo_url)
    except ValueError as e:
        return {"error": str(e)}

    local_path = clone_result["local_path"]
    repo_name = clone_result["repo_name"]

    scan_result = scan_repository(local_path)
    scan_result["repo_name"] = repo_name
    scan_result["owner"] = clone_result["owner"]
    scan_result["repo_url"] = request.repo_url

    graph = build_dependency_graph(
        scan_result["code_files"],
        parsed_sql_files=scan_result.get("sql_files")
    )

    graph_summary = get_graph_summary(graph)
    mermaid_diagram = generate_mermaid_diagram(graph)
    file_view = get_file_level_view(graph)

    # Store in memory
    REPO_STORE[repo_name] = {
        "graph": graph,
        "repo_data": scan_result,
        "graph_summary": graph_summary,
        "mermaid_diagram": mermaid_diagram,
    }

    # Persist metadata cache to SQLite
    try:
        save_repo_metadata(repo_name, clone_result["owner"], request.repo_url, scan_result)
    except Exception as e:
        print(f"[WARN] Failed to cache repo metadata to DB: {e}")

    # Extract clean relative paths for frontend display
    clean_file_nodes = [
        os.path.relpath(n, local_path).replace("\\", "/") if local_path in n else os.path.basename(n)
        for n in file_view.nodes
    ]

    from app.parsing.repo_scanner import build_ground_truth_catalog
    catalog = build_ground_truth_catalog(scan_result, graph)

    return {
        "repo_name": repo_name,
        "owner": clone_result["owner"],
        "total_files_parsed": scan_result["total_code_files"],
        "total_sql_files": scan_result["total_sql_files"],
        "tech_stack": scan_result["tech_stack"],
        "entry_points": scan_result["entry_points"],
        "directories": scan_result["directory_map"],
        "file_level_nodes": clean_file_nodes,
        "file_level_edges": list(file_view.edges),
        "graph_summary": graph_summary,
        "mermaid_diagram": mermaid_diagram,
        "catalog": catalog,
        "readme_snippet": scan_result.get("readme_content", "")[:500]
    }


@router.post("/chat")
def chat(request: ChatRequest):
    """
    Unified conversational endpoint that handles:
    - Pre-repo chit-chat & onboarding
    - Entire repo explanations
    - Directory mappings ('which directory does what?')
    - File connections & architectural flows
    - Specific file / function drill-down
    - Change blast-radius impact analysis
    """
    repo_entry = REPO_STORE.get(request.repo_name) if request.repo_name else None
    repo_data = repo_entry["repo_data"] if repo_entry else None
    graph = repo_entry["graph"] if repo_entry else None

    # Handle query
    result = route_and_execute_query(request.message, repo_data, graph)
    return result


@router.post("/ask")
def ask_question(request: QuestionRequest):
    """Answers a legacy question about a specific function in a cloned repo."""
    repo_entry = REPO_STORE.get(request.repo_name)
    if not repo_entry:
        return {"error": f"Repo '{request.repo_name}' not found. Please clone it first using /clone."}

    full_message = f"{request.question} in {request.file_path}::{request.function_name}"
    result = route_and_execute_query(full_message, repo_entry["repo_data"], repo_entry["graph"])
    return {"answer": result.get("answer")}