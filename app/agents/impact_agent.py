import os
from dotenv import load_dotenv
from app.agents.explainer_agent import run_completion, get_length_instruction

load_dotenv()

MAX_DEPENDENTS_IN_PROMPT = 15


def explain_impact(target_node: str, impact_data: dict, length_mode: str = "normal") -> str:
    """
    Takes BFS traversal result (from find_impact) and generates an
    actionable explanation of change blast radius, prioritized risk, and testing advice.
    """
    if "error" in impact_data:
        return f"⚠️ {impact_data['error']}"

    dependents = impact_data.get("all_dependents", [])
    if not dependents:
        return (
            f"✅ **Zero External Dependents Found**\n\n"
            f"Good news — nothing else in the parsed dependency graph directly or indirectly calls/imports `{target_node}`. "
            f"It appears safe to refactor or modify without immediate ripple effects."
        )

    length_rule = get_length_instruction(length_mode)
    sorted_dependents = sorted(dependents, key=lambda d: d["distance"])
    shown_dependents = sorted_dependents[:MAX_DEPENDENTS_IN_PROMPT]
    remaining_count = len(sorted_dependents) - len(shown_dependents)

    dependents_text = "\n".join(
        f"- `{d['node']}` (type: {d['type']}, distance: {d['distance']} step(s) away)"
        for d in shown_dependents
    )

    if remaining_count > 0:
        dependents_text += f"\n...and {remaining_count} more affected component(s) (high blast radius)."

    prompt = f"""You are a principal engineer assessing change risk and blast radius.

Target Item to Modify: `{target_node}`
Total Downstream Affected Items: {len(sorted_dependents)}

Direct & Indirect Dependents (ordered by distance):
{dependents_text}

Task:
Write a practical impact assessment:
1. **Direct Impact**: Which modules/functions will break immediately if the signature or behavior changes?
2. **Ripple Effect**: How far does the blast radius spread into the rest of the application?
3. **Recommended Testing & Safety Precautions**: What specific integration tests or unit tests should be verified before deploying changes?

Instruction on length: {length_rule}
Format with clean GitHub Markdown.
"""
    tokens = 300 if length_mode == "concise" else (800 if length_mode == "detailed" else 500)
    return run_completion(prompt, max_tokens=tokens, temperature=0.3)