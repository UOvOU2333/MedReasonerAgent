from tools.trace import append_trace


def doc_notifier_agent(state):
    """
    文档存储完成后的通知步骤。
    汇总保存结果，更新状态。
    """
    metadata = state.get("doc_metadata", {})
    storage_path = state.get("storage_path", "")
    validation_result = state.get("validation_result", {})
    language = state.get("language", "zh")

    if language == "zh":
        summary_lines = [
            f"✅ 文档已保存至：`{storage_path}`",
            f"- 文档名称：{metadata.get('doc_name', 'N/A')}",
            f"- 文档类型：{metadata.get('doc_type', 'N/A')}",
            f"- 版本：{metadata.get('version', 'N/A')}",
            f"- 大小：{metadata.get('size_chars', 0)} 字符",
            f"- 验证状态：{'通过' if validation_result.get('valid') else '需审核'}",
            f"- 创建时间：{metadata.get('created_at', 'N/A')}",
            "",
            "> 虚拟文档系统已接收并存储此文档。",
        ]
    else:
        summary_lines = [
            f"✅ Document saved to: `{storage_path}`",
            f"- Name: {metadata.get('doc_name', 'N/A')}",
            f"- Type: {metadata.get('doc_type', 'N/A')}",
            f"- Version: {metadata.get('version', 'N/A')}",
            f"- Size: {metadata.get('size_chars', 0)} chars",
            f"- Validation: {'Passed' if validation_result.get('valid') else 'Needs Review'}",
            f"- Created: {metadata.get('created_at', 'N/A')}",
            "",
            "> Virtual Document System has received and stored this document.",
        ]

    notification = {
        "success": True,
        "storage_path": storage_path,
        "summary": "\n".join(summary_lines),
    }

    state["notification"] = notification
    state["answer"] = notification["summary"]
    state["index_status"] = {"updated": True, "path": "generated_docs/index.json"}

    append_trace(state, "doc_notifier", f"Notified: {storage_path}")
    return state
