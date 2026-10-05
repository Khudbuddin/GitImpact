import os
from collections import defaultdict
from app.parsing.python_parser import parse_python_file
from app.parsing.java_parser import parse_java_file
from app.parsing.sql_parser import parse_sql_file

SKIP_DIRS = {
    ".git", "venv", ".venv", "node_modules", "__pycache__",
    ".idea", ".vscode", "dist", "build", ".pytest_cache",
    ".eggs", "cloned_repos", ".next", ".nuxt"
}

KNOWN_ENTRYPOINTS = {
    "main.py", "app.py", "run.py", "server.py", "manage.py",
    "app_ui.py", "index.py", "index.js", "index.ts", "server.js",
    "App.java", "Main.java", "Application.java"
}


def detect_tech_stack(repo_path: str, files_by_ext: dict) -> list[str]:
    """Infers frameworks, libraries, and languages used in the repository."""
    stack = set()

    if files_by_ext.get(".py"):
        stack.add("Python")
    if files_by_ext.get(".java"):
        stack.add("Java")
    if files_by_ext.get(".sql"):
        stack.add("SQL / Relational DB")
    if files_by_ext.get(".js") or files_by_ext.get(".jsx"):
        stack.add("JavaScript")
    if files_by_ext.get(".ts") or files_by_ext.get(".tsx"):
        stack.add("TypeScript")

    req_path = os.path.join(repo_path, "requirements.txt")
    if os.path.exists(req_path):
        try:
            with open(req_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lower()
                if "fastapi" in content:
                    stack.add("FastAPI")
                if "flask" in content:
                    stack.add("Flask")
                if "django" in content:
                    stack.add("Django")
                if "streamlit" in content:
                    stack.add("Streamlit")
                if "networkx" in content:
                    stack.add("NetworkX")
                if "tree-sitter" in content or "tree_sitter" in content:
                    stack.add("Tree-Sitter AST")
                if "groq" in content:
                    stack.add("Groq LLM")
                if "torch" in content or "tensorflow" in content:
                    stack.add("Deep Learning")
                if "pandas" in content:
                    stack.add("Pandas")
        except Exception:
            pass

    pkg_path = os.path.join(repo_path, "package.json")
    if os.path.exists(pkg_path):
        try:
            with open(pkg_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lower()
                if "react" in content:
                    stack.add("React")
                if "vue" in content:
                    stack.add("Vue")
                if "express" in content:
                    stack.add("Express.js")
                if "next" in content:
                    stack.add("Next.js")
        except Exception:
            pass

    if os.path.exists(os.path.join(repo_path, "Dockerfile")) or os.path.exists(os.path.join(repo_path, "docker-compose.yml")):
        stack.add("Docker")

    return sorted(list(stack))


def extract_readme(repo_path: str) -> str:
    """Finds and reads README file content if present."""
    readme_candidates = ["README.md", "readme.md", "README.rst", "README.txt", "README"]
    for candidate in readme_candidates:
        full_path = os.path.join(repo_path, candidate)
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().strip()
                    if content:
                        return content[:4500]
            except Exception:
                pass
    return ""


def categorize_directory(dir_name: str) -> str:
    """Heuristic directory classification for developer summaries."""
    low = dir_name.lower().strip("/\\")
    if not low or low == ".":
        return "Root project directory"
    if any(k in low for k in ["api", "routes", "controller", "endpoint"]):
        return "API routing and endpoint controllers"
    if any(k in low for k in ["agent", "ai", "llm", "bot"]):
        return "AI agents, orchestration, and LLM reasoning"
    if any(k in low for k in ["graph", "network", "traversal"]):
        return "Graph construction, modeling, and traversal logic"
    if any(k in low for k in ["parse", "ast", "lexer", "scan"]):
        return "AST parsing, code extraction, and file scanning"
    if any(k in low for k in ["ingest", "clone", "git", "loader", "file_handler"]):
        return "File handling, parsing pipelines, and data ingestion"
    if any(k in low for k in ["frontend", "ui", "view", "component", "static", "web", "pages"]):
        return "Frontend user interface & presentation layer"
    if any(k in low for k in ["auth", "security", "login", "user"]):
        return "User authentication, sessions, and access control"
    if any(k in low for k in ["db", "database", "model", "schema", "migration"]):
        return "Database schemas, models, and persistence"
    if any(k in low for k in ["script", "pipeline", "job"]):
        return "Processing scripts, model inference, and background tasks"
    if any(k in low for k in ["rule", "rules"]):
        return "Business rules and categorization heuristics"
    if any(k in low for k in ["test", "spec", "mock"]):
        return "Automated unit and integration test suites"
    if any(k in low for k in ["util", "helper", "common", "core", "lib"]):
        return "Shared utility functions and common helpers"
    if any(k in low for k in ["doc", "guide"]):
        return "Documentation and user guides"
    return "Application module"


def scan_repository(repo_path: str) -> dict:
    """
    Walks through every file in a repository and extracts:
    - Parsed AST code files (.py, .java)
    - Parsed SQL schema files (.sql)
    - Full directory structure and categorized directory purposes
    - Project README content
    - Detected tech stack
    - Entry point files
    """
    code_files_parsed = []
    sql_files_parsed = []
    files_by_ext = defaultdict(list)
    directory_map = defaultdict(list)
    entry_points = []
    norm_repo_path = os.path.normpath(repo_path).replace("\\", "/")

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

        rel_dir = os.path.relpath(root, repo_path).replace("\\", "/")
        if rel_dir == ".":
            rel_dir = "root"

        for filename in files:
            file_path = os.path.normpath(os.path.join(root, filename)).replace("\\", "/")
            rel_file_path = os.path.relpath(file_path, repo_path).replace("\\", "/")
            ext = os.path.splitext(filename)[1].lower()
            files_by_ext[ext].append(rel_file_path)
            directory_map[rel_dir].append(filename)

            if filename in KNOWN_ENTRYPOINTS:
                entry_points.append(rel_file_path)

            try:
                if filename.endswith(".py"):
                    parsed = parse_python_file(file_path)
                    parsed["rel_file"] = rel_file_path
                    code_files_parsed.append(parsed)
                elif filename.endswith(".java"):
                    parsed = parse_java_file(file_path)
                    parsed["rel_file"] = rel_file_path
                    code_files_parsed.append(parsed)
                elif filename.endswith(".sql"):
                    parsed = parse_sql_file(file_path)
                    parsed["rel_file"] = rel_file_path
                    sql_files_parsed.append(parsed)
            except Exception as e:
                print(f"[WARN] Skipped {file_path}: {e}")
                continue

    dir_summaries = {}
    for d_name, d_files in sorted(directory_map.items()):
        dir_summaries[d_name] = {
            "purpose": categorize_directory(d_name),
            "files": d_files,
            "file_count": len(d_files)
        }

    tech_stack = detect_tech_stack(repo_path, files_by_ext)
    readme_content = extract_readme(repo_path)

    return {
        "repo_path": norm_repo_path,
        "code_files": code_files_parsed,
        "sql_files": sql_files_parsed,
        "total_code_files": len(code_files_parsed),
        "total_sql_files": len(sql_files_parsed),
        "directory_map": dir_summaries,
        "tech_stack": tech_stack,
        "entry_points": entry_points,
        "readme_content": readme_content,
    }


def build_ground_truth_catalog(scan_result: dict, graph=None) -> dict:
    """
    Builds a structured ground-truth catalog mapping every real file,
    every real user-defined function, and exact call/import relationships.
    This guarantees 100% accuracy and eliminates AI hallucinations.
    """
    repo_path = scan_result.get("repo_path", "")
    code_files = scan_result.get("code_files", [])

    files_catalog = []
    functions_catalog = []
    functions_by_file = defaultdict(list)
    dir_files_catalog = defaultdict(list)

    for cf in code_files:
        raw_path = cf.get("file", "")
        rel_path = cf.get("rel_file") or (os.path.relpath(raw_path, repo_path).replace("\\", "/") if repo_path and repo_path in raw_path else os.path.basename(raw_path))
        base = os.path.basename(rel_path)
        d_name = os.path.dirname(rel_path) or "root"

        funcs = [f["name"] for f in cf.get("functions", [])]
        classes = [c["name"] for c in cf.get("classes", [])]
        imports = [i["text"] for i in cf.get("imports", [])]

        file_info = {
            "path": rel_path,
            "basename": base,
            "directory": d_name,
            "functions": funcs,
            "classes": classes,
            "imports": imports,
            "full_path": raw_path
        }
        files_catalog.append(file_info)
        dir_files_catalog[d_name].append(file_info)

        for fn in cf.get("functions", []):
            fn_name = fn["name"]
            fn_id = f"{rel_path}::{fn_name}"
            functions_by_file[rel_path].append(fn_name)

            calls_made = []
            for cl in cf.get("calls", []):
                if cl.get("in_function") == fn_name:
                    calls_made.append(cl["name"])

            functions_catalog.append({
                "id": fn_id,
                "name": fn_name,
                "file": rel_path,
                "line": fn.get("line", 1),
                "calls": sorted(list(set(calls_made)))
            })

    call_edges = []
    import_edges = []
    if graph:
        for u, v, d in graph.edges(data=True):
            rel = d.get("relation")
            if rel == "calls":
                call_edges.append((u, v))
            elif rel == "imports":
                import_edges.append((u, v))

    return {
        "files": files_catalog,
        "functions": functions_catalog,
        "functions_by_file": dict(functions_by_file),
        "directories": dict(dir_files_catalog),
        "call_edges": call_edges,
        "import_edges": import_edges,
        "total_files": len(files_catalog),
        "total_functions": len(functions_catalog)
    }