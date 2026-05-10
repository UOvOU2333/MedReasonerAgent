def supervisor_agent(state):
    """
    决定流程策略（单跳 / 多跳 / 深度推理）
    """

    prompt = f"""
You are a supervisor for a biomedical KG reasoning system.

Query: {state['query']}

Decide workflow:
- simple
- multi-hop
- deep-reasoning
"""

    decision = call_llm(prompt)

    state["trace"].append({
        "node": "supervisor",
        "output": decision
    })

    state["plan"] = {"mode": decision}
    return state