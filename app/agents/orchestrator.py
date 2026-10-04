import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-120b"

# Keywords that strongly signal an impact-type question
IMPACT_KEYWORDS = ["break", "impact", "affect", "depend", "risk", "consequence", "ripple"]


def classify_intent(user_question: str) -> str:
    """
    Determines whether the user wants a code EXPLANATION or a
    CHANGE-IMPACT analysis, based on their natural language question.

    Uses a fast rule-based keyword check first (cheap, reliable for
    obvious cases), and only falls back to the LLM for ambiguous questions.
    """
    question_lower = user_question.lower()

    # Rule-based fast path
    if any(keyword in question_lower for keyword in IMPACT_KEYWORDS):
        return "impact"

    prompt = f"""Classify the following user question into exactly one category:
- explain: the user wants to understand what a piece of code does
- impact: the user wants to know what would break or be affected if they change something

Question: "{user_question}"

Respond with ONLY the single word explain or impact, nothing else.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=10,
    )

    intent = response.choices[0].message.content.strip().lower()
    print(f"[DEBUG] Raw classification response: '{intent}'")  # temporary, remove later
    return "impact" if "impact" in intent else "explain"


def handle_user_question(user_question: str, file_path: str, function_name: str, graph) -> str:
    from app.parsing.python_parser import get_function_source
    from app.agents.explainer_agent import explain_code
    from app.agents.impact_agent import explain_impact
    from app.graph.traversal import find_impact

    intent = classify_intent(user_question)
    target_node = f"{file_path}::{function_name}"

    if intent == "explain":
        code = get_function_source(file_path, function_name)
        if not code:
            return f"Could not find function '{function_name}' in {file_path}."
        return explain_code(code, function_name)

    else:
        impact_data = find_impact(graph, target_node)
        if "error" in impact_data:
            return impact_data["error"]
        return explain_impact(target_node, impact_data)


if __name__ == "__main__":
    from app.parsing.python_parser import parse_python_file
    from app.graph.builder import build_dependency_graph

    files_to_test = ["app/ingestion/cloner.py", "app/parsing/python_parser.py"]
    parsed_data = [parse_python_file(f) for f in files_to_test]
    g = build_dependency_graph(parsed_data)

    q1 = "What does the clone_repository function do?"
    print("Q1:", q1)
    print("A1:", handle_user_question(q1, "app/ingestion/cloner.py", "clone_repository", g))

    print("\n---\n")

    q2 = "What will break if I change get_text?"
    print("Q2:", q2)
    print("A2:", handle_user_question(q2, "app/parsing/python_parser.py", "get_text", g))