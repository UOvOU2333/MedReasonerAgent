from tools.llm import call_llm
from tools.trace import append_trace


def doc_supervisor_agent(state):
    """
    文档生成智能体入口：判断用户请求的文档类型。
    支持：requirements（需求分析）、architecture（架构设计）、testing（测试文档）
    """
    language = state.get("language", "zh")
    query = state.get("query", "")
    doc_type_hint = state.get("doc_type", "")

    # 从 query 或 doc_type 推断文档类型
    prompt = f"""
You are a document generation supervisor. Classify the user's request into one of three document types:

1. requirements - 需求分析文档 (requirements analysis)
2. architecture - 架构设计文档 (architecture design)
3. testing - 测试文档 (test plan)

Request: {query}
Pre-set doc_type: {doc_type_hint}

Return ONLY one of: requirements, architecture, testing.
"""
    classification = call_llm(prompt, metadata={"agent_system": "docgen"}).strip().lower()

    # 兜底：用预设的 doc_type，若都无效则默认 requirements
    if classification not in ("requirements", "architecture", "testing"):
        if doc_type_hint in ("requirements", "architecture", "testing"):
            classification = doc_type_hint
        else:
            classification = "requirements"

    state["doc_type"] = classification

    doc_type_names = {
        "requirements": "需求分析文档",
        "architecture": "架构设计文档",
        "testing": "测试文档",
    }
    state["plan"] = {
        "mode": classification,
        "doc_type_name": doc_type_names.get(classification, classification),
        "spec_version": "V1.0",
    }

    append_trace(state, "doc_supervisor", f"Document type: {classification}")
    return state
