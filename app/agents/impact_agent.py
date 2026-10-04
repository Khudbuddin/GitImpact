import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-120b"

MAX_DEPENDENTS_IN_PROMPT = 15  # keeps the request well within token limits


def explain_impact(target_node: str, impact_data: dict) -> str:
    """
    Takes the raw traversal result (from find_impact) and generates a
    plain-English explanation of what would be affected by changing
    the target, and why it matters.
    """
    dependents = impact_data.get("all_dependents", [])

    if not dependents:
        return f"Good news — nothing in the codebase currently depends on '{target_node}'. It appears safe to modify without breaking other parts."

    # Sort by distance (closest/most directly affected first) and cap the list
    sorted_dependents = sorted(dependents, key=lambda d: d["distance"])
    shown_dependents = sorted_dependents[:MAX_DEPENDENTS_IN_PROMPT]
    remaining_count = len(sorted_dependents) - len(shown_dependents)

    dependents_text = "\n".join(
        f"- {d['node']} (type: {d['type']}, {d['distance']} step(s) away)"
        for d in shown_dependents
    )

    if remaining_count > 0:
        dependents_text += f"\n...and {remaining_count} more affected item(s) not shown here (this is a heavily-used piece of code)."

    prompt = f"""You are a senior developer explaining code change risk to a teammate.

A developer wants to change: {target_node}

The following parts of the codebase depend on it, directly or indirectly (showing the closest {len(shown_dependents)} out of {len(sorted_dependents)} total affected items):
{dependents_text}

Write a short, clear explanation (3-5 sentences) of what could break if this is changed, prioritizing the most directly connected items first. If there are many more affected items not shown, mention that this indicates the code is widely relied upon and changes should be made carefully. Be practical — mention what the developer should test or review before making this change. Do not just list the items again, actually explain the risk in plain English.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300,
    )

    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    from app.parsing.python_parser import parse_python_file
    from app.graph.builder import build_dependency_graph
    from app.graph.traversal import find_impact

    files_to_test = ["app/ingestion/cloner.py", "app/parsing/python_parser.py"]
    parsed_data = [parse_python_file(f) for f in files_to_test]
    g = build_dependency_graph(parsed_data)

    target = "app/parsing/python_parser.py::get_text"
    impact_result = find_impact(g, target)

    explanation = explain_impact(target, impact_result)
    print("Impact Explanation:\n", explanation)