from tools.trace import append_trace


def ranking_agent(state):
    """
    路径排序 Agent：
    - EMR 模式：drg_result 已含置信度，无须再排
    - NLP 模式：基于规则覆盖率的 Borda 计数排序
    """
    paths = state.get("reasoning_paths", [])
    drg_result = state.get("drg_result", {})

    if drg_result and drg_result.get("drg") != "N/A":
        # EMR 模式：置信度已算好，附注评分等级
        conf = drg_result.get("confidence", 0)
        level = "高" if conf >= 0.9 else ("中" if conf >= 0.5 else "低")
        drg_result["confidence_level"] = level
        state["drg_result"] = drg_result
        append_trace(state, "ranking",
                     f"Confidence: {conf:.0%} ({level}), "
                     f"factors: {len(drg_result.get('reasoning_steps', []))} steps matched")
        return state

    # NLP 模式：简单评分占位符
    ranked = sorted(paths)
    state["ranked_paths"] = ranked
    append_trace(state, "ranking", ranked[:2])
    return state
