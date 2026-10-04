import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
_client = None


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


def run_completion(prompt: str, max_tokens: int = 800, temperature: float = 0.3) -> str:
    """Executes completion with graceful fallback if API key is not configured."""
    client = get_groq_client()
    if not client:
        return (
            "⚠️ **Groq API Key not detected.**\n\n"
            "Please configure your `GROQ_API_KEY` in the `.env` file to enable AI reasoning. "
            "You can get a free API key at [console.groq.com](https://console.groq.com)."
        )

    model = os.getenv("GROQ_MODEL", DEFAULT_MODEL)
    # Ensure minimum token headroom for reasoning models (e.g. gpt-oss-120b)
    effective_max_tokens = max(max_tokens, 750)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
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
        return "Be extremely concise. Provide a short 2-3 bullet point summary with minimal text."
    elif length_mode == "detailed":
        return "Provide a deep, comprehensive, structured explanation with sections, bullet points, technical details, and code walkthroughs."
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

    prompt = f"""You are GitImpact, an AI-powered code analysis and repository intelligence assistant.
A user says: "{user_message}"

Current status: {repo_status}

Respond in a warm, helpful, and professional tone.
Explain what you can do:
1. Analyze GitHub repositories in Python, Java, and SQL.
2. Explain the overall project architecture, directory structures, and entry points.
3. Show how files and functions connect and import each other.
4. Perform blast-radius impact analysis ("What breaks if I change function X?").

Keep your response friendly and inviting.
"""
    return run_completion(prompt, max_tokens=300, temperature=0.5)


def explain_repository_overview(repo_data: dict, length_mode: str = "normal") -> str:
    """Explains the entire repository: purpose, tech stack, key components, and flow."""
    length_rule = get_length_instruction(length_mode)
    readme_snippet = repo_data.get("readme_content", "")[:2500]
    tech_stack = ", ".join(repo_data.get("tech_stack", [])) or "Standard Software Stack"
    entry_points = ", ".join(repo_data.get("entry_points", [])) or "Standard entry modules"
    total_files = repo_data.get("total_code_files", 0)

    prompt = f"""You are a senior software architect explaining an entire GitHub repository to a developer.

Repository Name: {repo_data.get('repo_name')}
Detected Tech Stack: {tech_stack}
Total Code Files: {total_files}
Main Entry Points: {entry_points}

README / Documentation excerpt:
{readme_snippet if readme_snippet else "(No README was provided in repository)"}

Directory Structure Summary:
{list(repo_data.get('directory_map', {}).keys())}

Task:
Explain this project to the developer:
1. Core Mission & What this application actually does.
2. Technology Stack & Frameworks.
3. Architecture & Key Modules / Entry points.
4. How the software works from end to end.

Instruction on length: {length_rule}
Format with clean GitHub Markdown (headings, bold text, bullet points).
"""
    tokens = 400 if length_mode == "concise" else (1200 if length_mode == "detailed" else 750)
    return run_completion(prompt, max_tokens=tokens, temperature=0.3)


def explain_directories(directory_map: dict, length_mode: str = "normal") -> str:
    """Explains each directory in the repository and its role."""
    length_rule = get_length_instruction(length_mode)

    dir_listing = []
    for d_name, d_info in directory_map.items():
        files_sample = ", ".join(d_info.get("files", [])[:6])
        if len(d_info.get("files", [])) > 6:
            files_sample += f" ... (+{len(d_info['files']) - 6} more)"
        dir_listing.append(f"- **`{d_name}/`**: {d_info.get('purpose')}\n  *Files:* {files_sample}")

    dirs_text = "\n".join(dir_listing)

    prompt = f"""You are explaining the directory structure of a software project to a developer.

Here is the directory layout and files:
{dirs_text}

Task:
Explain what each directory is responsible for and how they collaborate.
Explain where developers should look for:
- API routes or user interfaces
- Core business logic or AI models
- Utilities, helpers, and schemas

Instruction on length: {length_rule}
Use clear markdown tables or bulleted sections.
"""
    tokens = 400 if length_mode == "concise" else (1000 if length_mode == "detailed" else 650)
    return run_completion(prompt, max_tokens=tokens, temperature=0.3)


def explain_architecture_and_flow(graph_summary: dict, mermaid_diagram: str, length_mode: str = "normal") -> str:
    """Explains how files connect and the architectural dependency flow."""
    length_rule = get_length_instruction(length_mode)
    hubs = [f"`{h['file']}` (imported by {h['imported_by_count']} files)" for h in graph_summary.get("top_hubs", [])]
    hubs_str = ", ".join(hubs) if hubs else "Evenly distributed dependencies"

    prompt = f"""You are a software architect analyzing the dependency graph and file connections of a codebase.

Codebase Graph Statistics:
- Total Code Files: {graph_summary.get('total_files')}
- Total Functions / Methods: {graph_summary.get('total_functions')}
- Total Import Relationships: {graph_summary.get('total_imports')}
- Total Function Calls: {graph_summary.get('total_calls')}
- Central Core Hubs (Most imported files): {hubs_str}

Task:
Explain how files are connected and how data / control flows through the codebase.
- Identify the core foundation modules vs consumer modules.
- Explain the direction of dependencies.
- Highlight any potential architectural bottlenecks or high-coupling files.

Instruction on length: {length_rule}
"""
    tokens = 400 if length_mode == "concise" else (1000 if length_mode == "detailed" else 650)
    explanation = run_completion(prompt, max_tokens=tokens, temperature=0.3)

    if mermaid_diagram:
        diagram_block = f"\n\n### Dependency Architecture Flowchart\n```mermaid\n{mermaid_diagram}\n```"
        return explanation + diagram_block

    return explanation


def explain_file(file_path: str, all_functions: list, length_mode: str = "normal") -> str:
    """Explains an entire code file and its functions."""
    if not all_functions:
        return f"The file `{file_path}` contains no functions or methods (it may contain configuration, constants, or data)."

    length_rule = get_length_instruction(length_mode)
    shown = all_functions[:8]
    combined_code = "\n\n".join(f"# Function: {f['name']}\n{f['source']}" for f in shown)

    prompt = f"""You are explaining the code file `{file_path}` to a developer.

Here are the functions in this file:
{combined_code}

Task:
Explain the overall purpose of this file, the role of each function, and how they work together.
Instruction on length: {length_rule}
"""
    tokens = 350 if length_mode == "concise" else (900 if length_mode == "detailed" else 550)
    return run_completion(prompt, max_tokens=tokens, temperature=0.3)


def explain_code(code_snippet: str, name: str, length_mode: str = "normal") -> str:
    """Explains a single function or code snippet."""
    length_rule = get_length_instruction(length_mode)
    prompt = f"""Explain what the following function does in plain English.

Function name: {name}

Code:
{code_snippet}

Instruction on length: {length_rule}
Do not repeat the code itself, explain its behavior, inputs, and outputs clearly.
"""
    tokens = 200 if length_mode == "concise" else (600 if length_mode == "detailed" else 350)
    return run_completion(prompt, max_tokens=tokens, temperature=0.3)