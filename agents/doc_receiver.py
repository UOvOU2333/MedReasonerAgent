from tools.trace import append_trace


def doc_receiver_agent(state):
    """
    虚拟文档系统入口：接收文档生成智能体传来的文档内容。
    从上游（文档生成智能体）获取文档内容。
    """
    doc_content = state.get("doc_content", "")
    doc_name = state.get("doc_name", "untitled")
    doc_type = state.get("doc_type", "unknown")

    if not doc_content:
        # 如果没有传入文档内容，生成一个占位说明
        doc_content = (
            f"# {doc_name}\n\n"
            "> 此文档由虚拟文档系统智能体接收，暂无内容。\n"
            "> 请通过文档生成智能体生成文档后存入。\n"
        )

    # 如果没有指定 doc_name，从内容提取标题
    if doc_name == "untitled" or not doc_name:
        for line in doc_content.split("\n"):
            if line.startswith("# "):
                doc_name = line[2:].strip()
                break

    state["doc_content"] = doc_content
    state["doc_name"] = doc_name

    append_trace(state, "doc_receiver",
                 f"Received document: {doc_name} ({len(doc_content)} chars, type: {doc_type})")
    return state
