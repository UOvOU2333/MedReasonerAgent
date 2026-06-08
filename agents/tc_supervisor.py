from tools.llm import call_llm
from tools.trace import append_trace


def tc_supervisor_agent(state):
    """
    测试用例生成智能体入口：判断用户请求的测试用例类型。
    支持：normal（正常场景）、boundary（边界场景）、abnormal（异常场景）
    """
    language = state.get("language", "zh")
    query = state.get("query", "")
    tc_type_hint = state.get("tc_type", "")

    # 从 query 或 tc_type 推断测试用例类型
    prompt = f"""
You are a test case generation supervisor. Classify the user's request into one of three test case types:

1. normal - 正常场景测试用例 (normal scenario: valid diagnosis + procedure combinations)
2. boundary - 边界场景测试用例 (boundary scenario: comorbidities, age limits, gender differences)
3. abnormal - 异常场景测试用例 (abnormal scenario: code errors, missing info, logic conflicts)

Request: {query}
Pre-set tc_type: {tc_type_hint}

Return ONLY one of: normal, boundary, abnormal.
"""
    classification = call_llm(prompt, metadata={"agent_system": "tcgen"}).strip().lower()

    # 兜底：用预设的 tc_type，若都无效则默认 normal
    if classification not in ("normal", "boundary", "abnormal"):
        if tc_type_hint in ("normal", "boundary", "abnormal"):
            classification = tc_type_hint
        else:
            classification = "normal"

    state["tc_type"] = classification

    tc_type_names = {
        "normal": "正常场景测试用例",
        "boundary": "边界场景测试用例",
        "abnormal": "异常场景测试用例",
    }
    state["plan"] = {
        "mode": classification,
        "tc_type_name": tc_type_names.get(classification, classification),
        "spec_version": "V1.0",
    }

    append_trace(state, "tc_supervisor", f"Test case type: {classification}")
    return state
