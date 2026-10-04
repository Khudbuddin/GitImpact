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

    # Language inference
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

    # Dependency file inspections
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
                        # Return first 4500 characters
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
    if any(k in low for k in ["ingest", "clone", "git", "loader"]):
        return "Repository ingestion and cloning"
    if any(k in low for k in ["frontend", "ui", "view", "component", "static", "web"]):
        return "Frontend user interface & presentation layer"
    if any(k in low for k in ["db", "database", "model", "schema", "migration"]):
        return "Database schemas, models, and persistence"
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
        # Filter out directories in-place
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
                    code_files_parsed.append(parse_python_file(file_path))
                elif filename.endswith(".java"):
                    code_files_parsed.append(parse_java_file(file_path))
                elif filename.endswith(".sql"):
                    sql_files_parsed.append(parse_sql_file(file_path))
            except Exception as e:
                print(f"[WARN] Skipped {file_path}: {e}")
                continue

    # Directory summary with descriptions
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


if __name__ == "__main__":
    import json
    result = scan_repository("app")
    print(json.dumps({
        "total_code_files": result["total_code_files"],
        "tech_stack": result["tech_stack"],
        "directories": list(result["directory_map"].keys())
    }, indent=2))