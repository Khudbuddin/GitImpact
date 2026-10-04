from fastapi import APIRouter
from pydantic import BaseModel

from app.ingestion.cloner import clone_repository
from app.parsing.repo_scanner import scan_repository
from app.graph.builder import build_dependency_graph, get_file_level_view
from app.agents.orchestrator import handle_user_question

router = APIRouter()

# Simple in-memory store: repo_name -> built graph
# (Fine for a semester project demo; a real product would use a database/cache instead)
GRAPH_STORE = {}


class CloneRequest(BaseModel):
    repo_url: str


class QuestionRequest(BaseModel):
    repo_name: str
    file_path: str
    function_name: str
    question: str

class ChatRequest(BaseModel):
    repo_name: str
    message: str
    file_path: str | None = None


@router.post("/chat")
def chat(request: ChatRequest):
    graph = GRAPH_STORE.get(request.repo_name)
    if graph is None:
        return {"error": f"Repo '{request.repo_name}' not found."}

    from app.parsing.python_parser import parse_python_file, get_all_function_sources
    from app.agents.explainer_agent import explain_file, explain_code
    from app.agents.impact_agent import explain_impact
    from app.graph.traversal import find_impact

    file_path = request.file_path
    question_lower = request.message.lower()

    # Try to detect which known function the user is asking about
    target_function = None
    if file_path:
        parsed = parse_python_file(file_path)
        for func in parsed["functions"]:
            if func["name"].lower() in question_lower:
                target_function = func["name"]
                break

    if not file_path:
        return {"needs_file": True, "message": "Which file are you asking about?"}

    if target_function:
        if any(k in question_lower for k in ["break", "impact", "affect", "depend", "risk"]):
            impact_data = find_impact(graph, f"{file_path}::{target_function}")
            answer = explain_impact(f"{file_path}::{target_function}", impact_data)
        else:
            from app.parsing.python_parser import get_function_source
            code = get_function_source(file_path, target_function)
            answer = explain_code(code, target_function)
    else:
        all_functions = get_all_function_sources(file_path)
        answer = explain_file(file_path, all_functions)

    return {"answer": answer}

@router.get("/health")
def health_check():
    return {"status": "GitImpact API is alive"}


@router.post("/clone")
def clone_and_analyze(request: CloneRequest):
    """
    Clones the given repo, parses every file, builds the dependency
    graph, and stores it in memory for later questions.
    """
    try:
        local_path = clone_repository(request.repo_url)
    except ValueError as e:
        return {"error": str(e)}

    scan_result = scan_repository(local_path)
    graph = build_dependency_graph(scan_result["code_files"])

    repo_name = local_path.split("/")[-1]
    GRAPH_STORE[repo_name] = graph

    file_view = get_file_level_view(graph)

    return {
        "repo_name": repo_name,
        "total_files_parsed": scan_result["total_code_files"],
        "total_sql_files": scan_result["total_sql_files"],
        "file_level_nodes": list(file_view.nodes),
        "file_level_edges": list(file_view.edges),
    }


@router.post("/ask")
def ask_question(request: QuestionRequest):
    """
    Answers a question about a specific function in a previously
    cloned repo — either an explanation or a change-impact analysis.
    """
    graph = GRAPH_STORE.get(request.repo_name)
    if graph is None:
        return {"error": f"Repo '{request.repo_name}' not found. Clone it first using /clone."}

    answer = handle_user_question(
        request.question,
        request.file_path,
        request.function_name,
        graph
    )
    return {"answer": answer}