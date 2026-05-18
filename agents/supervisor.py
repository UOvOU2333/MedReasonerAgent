from tools.llm import call_llm
from tools.trace import append_trace


def supervisor_agent(state):
    """
    决定流程策略（单跳 / 多跳 / 深度推理）
    """

    language = "Chinese" if state.get("language") == "zh" else "English"
    prompt = f"""
You are a supervisor for a biomedical KG reasoning system.

Query: {state['query']}

Decide workflow:
- simple
- multi-hop
- deep-reasoning

Reply in {language}.
"""

    decision = call_llm(prompt)

    append_trace(state, "supervisor", decision)

    state["plan"] = {"mode": decision}
    return state
