from tools.llm import call_llm
from tools.trace import append_trace


def supervisor_agent(state):
    """
    决定流程策略：
    - 若 entity 已检测到 EMR 输入 → drg-grouper 模式
    - 否则 → LLM 判断 simple / multi-hop / deep-reasoning
    """
    if state.get("emr_data", {}).get("principal_dx_code"):
        state["plan"] = {"mode": "drg-grouper"}
        append_trace(state, "supervisor", "DRG grouper mode (structured EMR detected)")
        return state

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
