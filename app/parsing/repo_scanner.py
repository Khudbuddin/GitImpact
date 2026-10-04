import os
from app.parsing.python_parser import parse_python_file
from app.parsing.java_parser import parse_java_file
from app.parsing.sql_parser import parse_sql_file


def scan_repository(repo_path: str) -> dict:
    """
    Walks through every file in a cloned repository and parses
    each supported file type (.py, .java, .sql).

    Returns code files (for the dependency graph) separately from
    SQL schema files (for database impact tracing).
    """
    code_files_parsed = []
    sql_files_parsed = []

    skip_dirs = {".git", "venv", "node_modules", "__pycache__", ".idea", ".vscode"}

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]  # don't walk into irrelevant folders

        for filename in files:
            file_path = os.path.join(root, filename)

            try:
                if filename.endswith(".py"):
                    code_files_parsed.append(parse_python_file(file_path))
                elif filename.endswith(".java"):
                    code_files_parsed.append(parse_java_file(file_path))
                elif filename.endswith(".sql"):
                    sql_files_parsed.append(parse_sql_file(file_path))
            except Exception as e:
                # One broken/unusual file shouldn't crash the whole scan
                print(f"[WARN] Skipped {file_path}: {e}")
                continue

    return {
        "code_files": code_files_parsed,
        "sql_files": sql_files_parsed,
        "total_code_files": len(code_files_parsed),
        "total_sql_files": len(sql_files_parsed),
    }


if __name__ == "__main__":
    import json
    # Test on your own project's app/ folder — real multi-file structure, guaranteed to work
    result = scan_repository("app")
    print(json.dumps(result, indent=2))