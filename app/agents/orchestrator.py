import os
import re
from app.agents.explainer_agent import (
    explain_general_chat,
    explain_repository_overview,
    explain_directories,
    explain_architecture_and_flow,
    explain_file,
    explain_code,
    run_completion,
    get_length_instruction
)
from app.agents.impact_agent import explain_impact
from app.graph.traversal import find_impact
from app.graph.builder import get_graph_summary, generate_mermaid_diagram


IMPACT_KEYWORDS = ["break", "impact", "affect", "depend", "risk", "consequence", "ripple", "blast radius"]
OVERVIEW_KEYWORDS = ["whole repo", "entire repo", "project overview", "what does this project do", "what is this repo", "explain repo", "summary of repo", "explain the project", "about the project"]
DIRECTORY_KEYWORDS = ["which directory", "what directory", "directory structure", "folder structure", "explain directories", "explain folders", "what folders", "folder layout"]
ARCHITECTURE_KEYWORDS = ["how are files connected", "how files connected", "how are files related", "architecture", "file connections", "dependency flow", "data flow", "control flow", "how does the thing go", "how the thing goes", "workflow"]
GREETING_KEYWORDS = ["hi", "hello", "hey", "help", "who are you", "what can you do", "good morning", "good evening", "how to use"]


def detect_length_mode(user_question: str) -> str:
    """Detects whether the user wants a concise summary, a deep dive, or normal output."""
    q_low = user_question.lower()
    if any(k in q_low for k in ["brief", "short", "quick", "in 1 line", "in 2 lines", "summary only", "tldr", "succinct"]):
        return "concise"
    if any(k in q_low for k in ["deep", "deeply", "detailed", "step by step", "thorough", "in-depth", "in depth", "comprehensive", "everything", "walk me through"]):
        return "detailed"
    return "normal"


def classify_query_intent(user_question: str, has_repo: bool = False) -> str:
    """Classifies user intent into a specific routing category."""
    q_low = user_question.lower().strip()

    # If no repo loaded yet and user says hello or asks about the tool
    if not has_repo or any(q_low == g or q_low.startswith(f"{g} ") for g in GREETING_KEYWORDS):
        if not has_repo:
            return "CHIT_CHAT"

    # Impact query
    if any(k in q_low for k in IMPACT_KEYWORDS):
        return "IMPACT_ANALYSIS"

    # Whole repo overview
    if any(k in q_low for k in OVERVIEW_KEYWORDS):
        return "REPO_OVERVIEW"

    # Directory layout
    if any(k in q_low for k in DIRECTORY_KEYWORDS):
        return "DIRECTORY_MAP"

    # Architecture and file connections
    if any(k in q_low for k in ARCHITECTURE_KEYWORDS):
        return "FILE_CONNECTIONS"

    return "GENERAL_REPO_QUERY"


def find_matching_file_or_function(question: str, repo_data: dict) -> tuple[str | None, str | None]:
    """Finds if the user's prompt specifically mentions a known file or function."""
    q_low = question.lower()
    target_file = None
    target_func = None

    code_files = repo_data.get("code_files", [])
    for file_info in code_files:
        f_path = file_info.get("file", "")
        f_base = os.path.basename(f_path).lower()
        if f_base in q_low or f_path.lower() in q_low:
            target_file = f_path
            # Check for functions inside this file
            for func in file_info.get("functions", []):
                if func["name"].lower() in q_low:
                    target_func = func["name"]
                    break
            break

    # If no file found, check if a unique function was mentioned
    if not target_file:
        for file_info in code_files:
            for func in file_info.get("functions", []):
                pattern = r'\b' + re.escape(func["name"].lower()) + r'\b'
                if re.search(pattern, q_low):
                    target_file = file_info.get("file")
                    target_func = func["name"]
                    return target_file, target_func

    return target_file, target_func


def route_and_execute_query(user_question: str, repo_data: dict | None, graph=None) -> dict:
    """
    Central router that handles any question:
    - Pre-repo chit-chat
    - Whole repo overview
    - Directory purpose mapping
    - File connection graphs & flow
    - Specific file / function drill-down
    - Impact analysis
    - General free-form repo Q&A
    """
    has_repo = repo_data is not None and graph is not None
    intent = classify_query_intent(user_question, has_repo=has_repo)
    length_mode = detect_length_mode(user_question)

    # 1. Chit-chat / Onboarding
    if intent == "CHIT_CHAT" or not has_repo:
        repo_name = repo_data.get("repo_name") if repo_data else None
        answer = explain_general_chat(user_question, has_repo=has_repo, repo_name=repo_name)
        return {
            "answer": answer,
            "intent": "CHIT_CHAT",
            "diagram": None
        }

    # 2. Whole Repository Overview
    if intent == "REPO_OVERVIEW":
        answer = explain_repository_overview(repo_data, length_mode=length_mode)
        return {
            "answer": answer,
            "intent": "REPO_OVERVIEW",
            "diagram": None
        }

    # 3. Directory Mapping
    if intent == "DIRECTORY_MAP":
        directory_map = repo_data.get("directory_map", {})
        answer = explain_directories(directory_map, length_mode=length_mode)
        return {
            "answer": answer,
            "intent": "DIRECTORY_MAP",
            "diagram": None
        }

    # 4. Architecture and File Connections
    if intent == "FILE_CONNECTIONS":
        graph_summary = get_graph_summary(graph)
        mermaid_diag = generate_mermaid_diagram(graph)
        answer = explain_architecture_and_flow(graph_summary, mermaid_diag, length_mode=length_mode)
        return {
            "answer": answer,
            "intent": "FILE_CONNECTIONS",
            "diagram": mermaid_diag
        }

    # Check if a specific file or function was mentioned
    target_file, target_func = find_matching_file_or_function(user_question, repo_data)

    # 5. Impact Analysis
    if intent == "IMPACT_ANALYSIS":
        if target_func and target_file:
            node_id = f"{target_file}::{target_func}"
        elif target_file:
            node_id = target_file
        else:
            # Impact question asked without specifying target
            return {
                "answer": (
                    "To analyze change impact, please tell me which function or file you plan to modify!\n\n"
                    "For example: *'What breaks if I change `clone_repository`?'* or *'What depends on `routes.py`?'*"
                ),
                "intent": "IMPACT_PROMPT",
                "diagram": None
            }

        impact_data = find_impact(graph, node_id)
        answer = explain_impact(node_id, impact_data, length_mode=length_mode)
        return {
            "answer": answer,
            "intent": "IMPACT_ANALYSIS",
            "diagram": None
        }

    # 6. Specific File or Function
    if target_func and target_file:
        from app.parsing.python_parser import get_function_source
        from app.parsing.java_parser import get_java_method_source
        if target_file.endswith(".java"):
            code = get_java_method_source(target_file, target_func)
        else:
            code = get_function_source(target_file, target_func)

        if code:
            answer = explain_code(code, target_func, length_mode=length_mode)
            return {"answer": answer, "intent": "EXPLAIN_FUNCTION", "diagram": None}

    if target_file:
        from app.parsing.python_parser import get_all_function_sources
        from app.parsing.java_parser import get_all_java_method_sources
        if target_file.endswith(".java"):
            funcs = get_all_java_method_sources(target_file)
        else:
            funcs = get_all_function_sources(target_file)

        answer = explain_file(target_file, funcs, length_mode=length_mode)
        return {"answer": answer, "intent": "EXPLAIN_FILE", "diagram": None}

    # 7. General Free-form Repo Question
    # The user asked something else about the repo (e.g. "where is the database handled?", "how is auth done?")
    length_rule = get_length_instruction(length_mode)
    readme_snippet = repo_data.get("readme_content", "")[:1500]
    tech_stack = ", ".join(repo_data.get("tech_stack", []))
    dir_keys = list(repo_data.get("directory_map", {}).keys())

    prompt = f"""You are GitImpact, an AI repository assistant.
The user is asking a question about the repository `{repo_data.get('repo_name')}`:

User Question: "{user_question}"

Repository Context:
- Tech Stack: {tech_stack}
- Directories: {dir_keys}
- Main Entry Points: {repo_data.get('entry_points', [])}
- Documentation Excerpt:
{readme_snippet}

Task:
Answer the user's question clearly and accurately based on the codebase context.
Instruction on length: {length_rule}
Format with markdown.
"""
    tokens = 350 if length_mode == "concise" else (900 if length_mode == "detailed" else 550)
    answer = run_completion(prompt, max_tokens=tokens, temperature=0.3)
    return {
        "answer": answer,
        "intent": "GENERAL_REPO_QUERY",
        "diagram": None
    }