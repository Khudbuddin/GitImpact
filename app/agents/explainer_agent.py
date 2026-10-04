import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-120b"

def explain_code(code_snippet: str, name: str) -> str:
    """
    Sends a code snippet to the LLM and returns a short, plain-English
    explanation of what it does.
    """
    prompt = f"""You are a code explainer for developers. Explain what the following function does, in plain English, in 2-4 sentences. Do not repeat the code itself, just explain its purpose and behavior clearly.

Function name: {name}

Code:
{code_snippet}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=200,
    )

    return response.choices[0].message.content.strip()

MAX_FUNCTIONS_IN_FILE_SUMMARY = 10

def explain_file(file_path: str, all_functions: list) -> str:
    """
    Explains an ENTIRE file — its overall purpose and what each major
    function does — not just one function in isolation.
    """
    if not all_functions:
        return "This file has no functions to explain (it may only contain imports or constants)."

    shown = all_functions[:MAX_FUNCTIONS_IN_FILE_SUMMARY]
    remaining = len(all_functions) - len(shown)

    combined_code = "\n\n".join(f"# Function: {f['name']}\n{f['source']}" for f in shown)
    note = f"\n\n(There are {remaining} more functions in this file not shown here.)" if remaining > 0 else ""

    prompt = f"""You are explaining an entire code file to a developer who has never seen it.

Here are the functions in this file:
{combined_code}
{note}

Write a clear overview (5-8 sentences) covering: what this file's overall purpose is, what role each major function plays, and how they likely work together. Be thorough but readable — this should give someone a genuine understanding of the whole file, not just one piece of it.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    from app.parsing.python_parser import get_function_source

    code = get_function_source("app/ingestion/cloner.py", "clone_repository")
    if code:
        explanation = explain_code(code, "clone_repository")
        print("Explanation:\n", explanation)
    else:
        print("Function not found.")