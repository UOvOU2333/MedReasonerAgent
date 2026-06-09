from runtime.router import router
from tools.trace import append_trace


def reasoning_agent(state):
    """
    医学推理 Agent：
    - EMR 模式：drg_result 已在 retrieval 中生成，直接透传并计算置信度
    - NLP 模式：调用 LLM/SGLang 做自由推理
    """
    drg_result = state.get("drg_result", {})

    if drg_result and drg_result.get("drg") != "N/A":
        # EMR 模式：retrieval 已完成入组，这里组装推理路径字符串
        steps_text = "\n".join(drg_result.get("reasoning_steps", []))
        state["reasoning_paths"] = [steps_text]
        state["ranked_paths"] = [steps_text]
        append_trace(state, "reasoning",
                     f"DRG: {drg_result['drg']} confidence={drg_result.get('confidence', 0):.0%}")
        return state

    # NLP 模式：LLM 自由推理
    language = "Chinese" if state.get("language") == "zh" else "English"
    prompt = f"""
Biomedical reasoning:

Entities: {state['entities']}
Graph: {state['subgraph']}

Task:
- find multi-hop biological reasoning paths
- explain mechanism

Reply in {language}.
"""
    result = router.reason(prompt)
    state["reasoning_paths"] = [result]
    append_trace(state, "reasoning", result)
    return state
