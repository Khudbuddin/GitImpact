import os
import re
from app.agents.explainer_agent import (
    explain_general_chat,
    explain_repository_overview,
    explain_directories,
    explain_directory_specific,
    explain_all_files_one_by_one,
    explain_functions_in_file,
    explain_function_connections_and_pipeline,
    run_completion,
    get_length_instruction
)
from app.agents.impact_agent import explain_impact
from app.graph.traversal import find_impact
from app.graph.builder import get_graph_summary, generate_mermaid_diagram, generate_function_call_mermaid
from app.parsing.repo_scanner import build_ground_truth_catalog


def detect_length_mode(user_question: str) -> str:
    """Detects whether the user wants a concise summary, a deep dive, or normal output."""
    q_low = user_question.lower()
    if any(k in q_low for k in ["brief", "short", "quick", "in 1 line", "in 2 lines", "summary only", "tldr", "succinct"]):
        return "concise"
    if any(k in q_low for k in ["deep", "deeply", "detailed", "step by step", "thorough", "in-depth", "in depth", "comprehensive", "everything", "walk me through"]):
        return "detailed"
    return "normal"


def match_directory(question: str, directory_map: dict) -> str | None:
    """Finds if the user specifically asked about a particular directory (e.g. 'scripts', 'frontend', 'auth')."""
    q_low = question.lower()
    for d_name in directory_map.keys():
        d_base = os.path.basename(d_name.strip("/\\")).lower()
        if d_base and len(d_base) > 2 and (d_base in q_low or d_name.lower() in q_low):
            return d_name
    return None


def match_file_or_function(question: str, files_catalog: list) -> tuple[dict | None, str | None]:
    """Finds if a specific file or function is mentioned in the question."""
    q_low = question.lower()
    matched_file = None
    matched_func = None

    for f_info in files_catalog:
        f_base = f_info["basename"].lower()
        f_path = f_info["path"].lower()
        if f_base in q_low or f_path in q_low:
            matched_file = f_info
            for fn in f_info["functions"]:
                if fn.lower() in q_low:
                    matched_func = fn
                    break
            break

    # If no file was matched directly, check if a unique function name was mentioned
    if not matched_file:
        for f_info in files_catalog:
            for fn in f_info["functions"]:
                pattern = r'\b' + re.escape(fn.lower()) + r'\b'
                if re.search(pattern, q_low):
                    return f_info, fn

    return matched_file, matched_func


def route_and_execute_query(user_question: str, repo_data: dict | None, graph=None) -> dict:
    """
    Ground-Truth Driven Central Orchestrator.
    Routes queries with 100% real codebase facts:
    1. Chit-chat & onboarding
    2. Specific directory inquiry (e.g. 'what files in scripts folder?')
    3. File-by-file walkthrough (e.g. 'explain each file one by one')
    4. Function-to-function connection & data flow pipeline
    5. User-defined functions inside a file
    6. Change blast-radius impact analysis
    7. Overall project architecture & directory mapping
    8. Freeform grounded code Q&A
    """
    has_repo = repo_data is not None and graph is not None
    q_low = user_question.lower().strip()
    length_mode = detect_length_mode(user_question)

    # 1. Chit-chat / No repo
    greeting_triggers = ["hi", "hello", "hey", "help", "who are you", "what can you do", "how to use", "start"]
    if not has_repo or any(q_low == g or q_low.startswith(f"{g} ") for g in greeting_triggers):
        if not has_repo:
            repo_name = repo_data.get("repo_name") if repo_data else None
            answer = explain_general_chat(user_question, has_repo=has_repo, repo_name=repo_name)
            return {"answer": answer, "intent": "CHIT_CHAT", "diagram": None}

    # Build Ground Truth Catalog
    catalog = build_ground_truth_catalog(repo_data, graph)
    files_catalog = catalog["files"]
    call_edges = catalog["call_edges"]
    directory_map = repo_data.get("directory_map", {})

    # Check for matched file, function, or directory
    matched_file, matched_func = match_file_or_function(user_question, files_catalog)
    matched_dir = match_directory(user_question, directory_map)

    # 2. Specific Directory Inquiry (e.g. "what files in scripts folder", "tell me about frontend folder")
    if matched_dir:
        files_in_dir = [f for f in files_catalog if f["directory"] == matched_dir or f["directory"].endswith(matched_dir)]
        dir_purpose = directory_map.get(matched_dir, {}).get("purpose", "Application module")
        answer = explain_directory_specific(matched_dir, files_in_dir, dir_purpose, length_mode=length_mode)
        return {
            "answer": answer,
            "intent": "DIRECTORY_SPECIFIC",
            "diagram": None,
            "matched_dir": matched_dir
        }

    # 3. Explain Each File One by One (e.g. "explain each file in the given repo one by one")
    if any(k in q_low for k in ["each file", "all files", "file by file", "one by one", "24 files", "all 24", "explain every file"]):
        answer = explain_all_files_one_by_one(files_catalog, length_mode=length_mode)
        return {
            "answer": answer,
            "intent": "ALL_FILES_WALKTHROUGH",
            "diagram": None
        }

    # 4. User-Defined Functions Query (e.g. "i told functions user define functions in a particular file", "what functions in dashboard.py")
    if any(k in q_low for k in ["user define function", "user defined function", "functions in", "what functions", "list functions"]):
        if matched_file:
            from app.parsing.python_parser import get_all_function_sources
            from app.parsing.java_parser import get_all_java_method_sources
            raw_path = matched_file["full_path"]
            if raw_path.endswith(".java"):
                sources = get_all_java_method_sources(raw_path)
            else:
                sources = get_all_function_sources(raw_path)

            answer = explain_functions_in_file(matched_file["path"], matched_file, sources, length_mode=length_mode)
            return {"answer": answer, "intent": "FUNCTIONS_IN_FILE", "diagram": None}
        else:
            # User asked about user-defined functions generally across the project
            total_funcs = catalog["total_functions"]
            sample_summary = []
            for f in files_catalog:
                if f["functions"]:
                    sample_summary.append(f"- **`{f['path']}`**: `{', '.join(f['functions'])}`")

            summary_text = "\n".join(sample_summary)
            answer = (
                f"### ⚡ User-Defined Functions in `{repo_data.get('repo_name')}`\n\n"
                f"There are **{total_funcs} user-defined functions** across the project:\n\n"
                f"{summary_text}\n\n"
                f"💡 *You can ask about any specific file or function (e.g. 'Explain the functions in `predicted.py`' or 'What does `process_file` do?')!*"
            )
            return {"answer": answer, "intent": "ALL_FUNCTIONS_SUMMARY", "diagram": None}

    # 5. Function Call Tree / Flow Chart Query (e.g. "tree chart", "how functions connected", "chart of functions")
    if any(k in q_low for k in ["tree chart", "function chart", "chart of all", "chart of functions", "function tree", "tree of functions", "call graph", "call chart", "diagram of functions", "how functions connected", "how are functions connected", "chart or anything that shows"]):
        mermaid_diag = generate_function_call_mermaid(graph) or generate_mermaid_diagram(graph)
        answer = explain_function_connections_and_pipeline(call_edges, files_catalog, length_mode=length_mode, include_tree=True)
        return {
            "answer": answer,
            "intent": "FUNCTION_TREE_CHART",
            "diagram": mermaid_diag
        }

    # 6. Function Connections & Execution Pipeline
    if any(k in q_low for k in ["how are files connected", "how files connected", "function connected", "another file output", "data flow", "how does the thing go", "pipeline", "architecture flow", "how there files"]):
        answer = explain_function_connections_and_pipeline(call_edges, files_catalog, length_mode=length_mode)
        mermaid_diag = generate_function_call_mermaid(graph) or generate_mermaid_diagram(graph)
        return {
            "answer": answer,
            "intent": "FUNCTION_PIPELINE",
            "diagram": mermaid_diag
        }

    # 7. Change Blast-Radius Impact Analysis
    if any(k in q_low for k in ["break", "impact", "affect", "depend", "risk", "consequence", "ripple", "blast radius"]):
        if matched_func and matched_file:
            node_id = f"{matched_file['full_path']}::{matched_func}"
        elif matched_file:
            node_id = matched_file["full_path"]
        else:
            return {
                "answer": (
                    "To analyze change blast radius, please specify the function or file you plan to modify!\n\n"
                    "For example: *'What breaks if I change `process_file`?'* or *'What depends on `database_manager.py`?'*"
                ),
                "intent": "IMPACT_PROMPT",
                "diagram": None
            }

        impact_data = find_impact(graph, node_id)
        answer = explain_impact(node_id, impact_data, length_mode=length_mode)
        return {"answer": answer, "intent": "IMPACT_ANALYSIS", "diagram": None}

    # 8. Whole Repo Overview / Directory Overview
    if any(k in q_low for k in ["whole repo", "entire repo", "project overview", "what does this project do", "what is this repo", "explain repo", "summary of repo", "explain the project", "full description"]):
        answer = explain_repository_overview(repo_data, files_catalog, length_mode=length_mode)
        return {"answer": answer, "intent": "REPO_OVERVIEW", "diagram": None}

    if any(k in q_low for k in ["which directory", "what directory", "directory structure", "folder structure", "explain directories", "explain folders"]):
        answer = explain_directories(directory_map, length_mode=length_mode)
        return {"answer": answer, "intent": "DIRECTORY_MAP", "diagram": None}

    # 9. Single File or Function Drill-down
    if matched_func and matched_file:
        from app.parsing.python_parser import get_function_source
        from app.parsing.java_parser import get_java_method_source
        raw_path = matched_file["full_path"]
        code = get_java_method_source(raw_path, matched_func) if raw_path.endswith(".java") else get_function_source(raw_path, matched_func)
        if code:
            from app.agents.explainer_agent import explain_code
            answer = explain_code(code, matched_func, length_mode=length_mode)
            return {"answer": answer, "intent": "EXPLAIN_FUNCTION", "diagram": None}

    if matched_file:
        from app.parsing.python_parser import get_all_function_sources
        from app.parsing.java_parser import get_all_java_method_sources
        raw_path = matched_file["full_path"]
        sources = get_all_java_method_sources(raw_path) if raw_path.endswith(".java") else get_all_function_sources(raw_path)
        from app.agents.explainer_agent import explain_file
        answer = explain_file(matched_file["path"], sources, length_mode=length_mode)
        return {"answer": answer, "intent": "EXPLAIN_FILE", "diagram": None}

    # 10. Free-form Grounded Codebase Q&A
    length_rule = get_length_instruction(length_mode)
    functions_summary = "\n".join(f"- `{f['path']}`: {', '.join(f['functions'])}" for f in files_catalog if f["functions"])
    call_sample = "\n".join(f"- `{os.path.basename(u.split('::')[0])}::{u.split('::')[-1]}` -> `{os.path.basename(v.split('::')[0])}::{v.split('::')[-1]}`" for u, v in call_edges[:25])

    prompt = f"""The user is asking a question about repository `{repo_data.get('repo_name')}`:

User Question: "{user_question}"

Ground Truth Context:
- Real Code Files: {[f['path'] for f in files_catalog]}
- Real User-Defined Functions by File:
{functions_summary}
- Real Function-to-Function Call Relationships:
{call_sample}
- Real Directories: {list(directory_map.keys())}
- README Snippet:
{repo_data.get('readme_content', '')[:1000]}

Task:
Answer accurately based ONLY on the real codebase facts above.
Instruction on length: {length_rule}
CRITICAL: You HAVE the exact functions and files above. NEVER say you don't have the list of functions.
Format with clean GitHub Markdown.
"""
    tokens = 600 if length_mode == "concise" else 1300
    answer = run_completion(prompt, max_tokens=tokens, temperature=0.2)
    return {"answer": answer, "intent": "GENERAL_REPO_QUERY", "diagram": None}