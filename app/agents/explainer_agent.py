import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
_client = None

STRICT_SYSTEM_DIRECTIVE = """You are GitImpact, a precise code intelligence engine.
CRITICAL ACCURACY DIRECTIVE:
1. You MUST ONLY reference real files, functions, and directories provided in the Ground Truth below.
2. NEVER invent, hallucinate, or guess file names (such as 'extract_text.py', 'process_receipt.py', 'predict_category.py', etc.) or function names.
3. Every file and function you mention MUST exist in the Ground Truth Catalog. If you do not have info on a file, state clearly that it is not in the parsed codebase.
"""


def get_groq_client():
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if api_key and api_key.strip():
            try:
                _client = Groq(api_key=api_key.strip())
            except Exception as e:
                print(f"[WARN] Failed to initialize Groq client: {e}")
                return None
    return _client


def run_completion(prompt: str, max_tokens: int = 1000, temperature: float = 0.2) -> str:
    """Executes completion with graceful fallback and reasoning model token headroom."""
    client = get_groq_client()
    if not client:
        return (
            "⚠️ **Groq API Key not detected.**\n\n"
            "Please configure your `GROQ_API_KEY` in the `.env` file to enable AI reasoning. "
            "You can get a free API key at [console.groq.com](https://console.groq.com)."
        )

    model = os.getenv("GROQ_MODEL", DEFAULT_MODEL)
    effective_max_tokens = max(max_tokens, 850)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": STRICT_SYSTEM_DIRECTIVE},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=effective_max_tokens,
        )
        msg = response.choices[0].message
        content = (msg.content or "").strip()
        if not content and hasattr(msg, "reasoning") and msg.reasoning:
            content = msg.reasoning.strip()
        return content or "No response generated."
    except Exception as e:
        return f"⚠️ **AI Service Error**: {e}"


def get_length_instruction(length_mode: str) -> str:
    if length_mode == "concise":
        return "Be concise and direct. Provide a brief 2-3 bullet point summary."
    elif length_mode == "detailed":
        return "Provide a deep, comprehensive, structured explanation with sections, bullet points, and exact function-level details."
    else:
        return "Provide a clear, well-balanced explanation with 4-8 structured sentences or bullet points."


def explain_general_chat(user_message: str, has_repo: bool = False, repo_name: str | None = None) -> str:
    """Handles conversational greetings and onboarding questions."""
    repo_status = (
        f"The repository **{repo_name}** is currently analyzed and ready for questions."
        if has_repo else
        "No repository has been analyzed yet. You can paste a public GitHub repository link anytime!"
    )

    client = get_groq_client()
    if not client:
        return (
            f"👋 **Hello! I'm GitImpact**, your AI codebase intelligence assistant.\n\n"
            f"**Status:** {repo_status}\n\n"
            f"**What I can do:**\n"
            f"1. 📥 **Clone & Parse Repositories**: Extract AST structures for Python (`.py`), Java (`.java`), and SQL schemas (`.sql`).\n"
            f"2. 🗺️ **Directory & Architecture Mapping**: Explain which directory does what and how files connect.\n"
            f"3. 💥 **Blast-Radius Impact Analysis**: Trace what breaks if you modify a function or file.\n\n"
            f"👉 Paste any public GitHub repo URL (e.g., `https://github.com/owner/repo`) to get started!"
        )

    prompt = f"""A user says: "{user_message}"
Current repository status: {repo_status}

Respond warmly and professionally. Explain your capabilities:
- Accurate AST file & function inspection (no hallucinations).
- Directory responsibility mapping.
- Function-to-function call dependency pipelines.
- Change blast-radius impact analysis.
"""
    return run_completion(prompt, max_tokens=350, temperature=0.4)


def explain_directory_specific(dir_name: str, files_in_dir: list, dir_purpose: str, length_mode: str = "normal") -> str:
    """Explains a specific directory and the EXACT files and functions inside it."""
    length_rule = get_length_instruction(length_mode)

    files_lines = []
    for f in files_in_dir:
        funcs_str = ", ".join(f.get("functions", [])) or "No functions (module/config)"
        files_lines.append(f"- **`{f['basename']}`** (path: `{f['path']}`)\n  - User-defined functions: `{funcs_str}`")

    files_block = "\n".join(files_lines)

    prompt = f"""The user is asking about the directory `{dir_name}`.

Directory Purpose: {dir_purpose}
Actual Files & Functions in this directory (Ground Truth):
{files_block}

Task:
Explain what the `{dir_name}` folder is responsible for in this repository.
For EACH of the real files listed above, explain:
1. What the file does.
2. What its user-defined functions do.
3. How it collaborates with other parts of the project.

CRITICAL: ONLY mention the real files listed above. Do NOT invent files!
Instruction on length: {length_rule}
Format with markdown headers and bullet points.
"""
    tokens = 450 if length_mode == "concise" else 1100
    return run_completion(prompt, max_tokens=tokens, temperature=0.2)


def explain_all_files_one_by_one(files_catalog: list, length_mode: str = "normal") -> str:
    """Explains every real file in the repository one by one."""
    length_rule = get_length_instruction(length_mode)

    catalog_lines = []
    for idx, f in enumerate(files_catalog, start=1):
        funcs_str = ", ".join(f.get("functions", [])) or "None (constants/init)"
        catalog_lines.append(f"{idx}. `{f['path']}` — Functions: [{funcs_str}]")

    catalog_block = "\n".join(catalog_lines)

    prompt = f"""The user wants an explanation of all {len(files_catalog)} code files in the repository one by one.

Here is the EXACT Ground Truth list of all files and their user-defined functions:
{catalog_block}

Task:
Walk through each file one by one in a structured table or numbered list:
- File path
- What it does in the project
- Key user-defined functions it contains

CRITICAL: ONLY describe the exact files listed above. Do NOT skip files or invent non-existent files.
Instruction on length: {length_rule}
"""
    return run_completion(prompt, max_tokens=1500, temperature=0.2)


def explain_functions_in_file(file_path: str, file_info: dict, all_functions_code: list, length_mode: str = "normal") -> str:
    """Explains all user-defined functions inside a specific file."""
    length_rule = get_length_instruction(length_mode)
    funcs = file_info.get("functions", [])
    if not funcs:
        return f"The file `{file_path}` contains no user-defined functions (it may only contain imports, UI layout, or configuration)."

    code_blocks = "\n\n".join(
        f"### Function: `{f['name']}`\n```python\n{f['source']}\n```"
        for f in all_functions_code[:10]
    )

    prompt = f"""Explain all user-defined functions inside the file `{file_path}`.

Real functions in this file:
{funcs}

Function Source Code:
{code_blocks}

Task:
For EACH user-defined function in `{file_path}`:
1. Explain what the function does and what inputs/outputs it takes.
2. What role it plays in the overall application workflow.
3. What other functions or modules it calls.

Instruction on length: {length_rule}
"""
    return run_completion(prompt, max_tokens=1200, temperature=0.2)


def explain_function_connections_and_pipeline(call_edges: list, files_catalog: list, length_mode: str = "normal") -> str:
    """Explains the exact function-to-function and file-to-file call pipeline."""
    length_rule = get_length_instruction(length_mode)

    edges_formatted = []
    for u, v in call_edges[:35]:
        u_clean = os.path.basename(u.split("::")[0]) + "::" + u.split("::")[-1]
        v_clean = os.path.basename(v.split("::")[0]) + "::" + v.split("::")[-1]
        edges_formatted.append(f"- `{u_clean}` ──(calls)──> `{v_clean}`")

    edges_block = "\n".join(edges_formatted) if edges_formatted else "Direct function calls mapped via modules."

    prompt = f"""The user wants to know how files and user-defined functions connect to each other, how execution flows, and how a function's output affects another file.

Here is the EXACT Function Call Graph extracted via AST analysis:
{edges_block}

Files in the repository:
{[f['path'] for f in files_catalog]}

Task:
Provide a clear, concrete breakdown:
1. **End-to-End Execution Flow**: How does data start from the entry point (e.g. UI / main) and flow through functions down to the backend loaders, models, and databases?
2. **Function-to-Function Connections**: Detail the specific call chains (e.g. Function A calls Function B to parse data, which returns output to Function C).
3. **Data Dependency**: Explain how changes in one function's return format would ripple into the next function that receives its output.

CRITICAL: ONLY mention the real functions and files in the call graph above. Do NOT invent functions!
Instruction on length: {length_rule}
"""
    return run_completion(prompt, max_tokens=1300, temperature=0.2)


def explain_repository_overview(repo_data: dict, files_catalog: list, length_mode: str = "normal") -> str:
    """Explains the repository purpose and real architecture."""
    length_rule = get_length_instruction(length_mode)
    readme_snippet = repo_data.get("readme_content", "")[:2500]
    tech_stack = ", ".join(repo_data.get("tech_stack", [])) or "Python"
    entry_points = ", ".join(repo_data.get("entry_points", [])) or "main.py"

    real_files_sample = [f["path"] for f in files_catalog[:15]]

    prompt = f"""Explain this repository to a developer.

Repository Name: {repo_data.get('repo_name')}
Detected Tech Stack: {tech_stack}
Entry Points: {entry_points}
Total Files: {len(files_catalog)}

Real Code Files in Project (Ground Truth):
{real_files_sample}

README Documentation:
{readme_snippet or "(No README provided)"}

Task:
Explain:
1. Core Mission & What this application does.
2. Architecture & How components work together.
3. Key Modules & Entry points.

Instruction on length: {length_rule}
CRITICAL: ONLY reference the real files listed above.
"""
    return run_completion(prompt, max_tokens=900, temperature=0.2)


def explain_directories(directory_map: dict, length_mode: str = "normal") -> str:
    """Explains each directory in the repository and its role."""
    length_rule = get_length_instruction(length_mode)

    dir_listing = []
    for d_name, d_info in directory_map.items():
        files_sample = ", ".join(d_info.get("files", [])[:8])
        dir_listing.append(f"- **`{d_name}/`**: {d_info.get('purpose')}\n  *Exact Files:* {files_sample}")

    dirs_text = "\n".join(dir_listing)

    prompt = f"""Explain the directory layout of this repository.

Ground Truth Directory Structure:
{dirs_text}

Task:
Explain what each directory is responsible for and how they collaborate.
CRITICAL: ONLY mention the real files in the directories above.
Instruction on length: {length_rule}
"""
    return run_completion(prompt, max_tokens=850, temperature=0.2)