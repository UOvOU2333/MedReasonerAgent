import json
from datetime import datetime, timezone
from tools.trace import append_trace


def doc_metadata_tagger_agent(state):
    """
    为文档打上元数据标签：版本号、创建时间、文档类型等。
    生成符合虚拟文档系统存储规范的元数据。
    """
    doc_name = state.get("doc_name", "untitled")
    doc_type = state.get("doc_type", "unknown")
    validation_result = state.get("validation_result", {})

    metadata = {
        "doc_name": doc_name,
        "doc_type": doc_type,
        "version": "V1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "language": state.get("language", "zh"),
        "status": "draft",
        "format": "markdown",
        "source": "DocGen Agent",
        "validation_status": "passed" if validation_result.get("valid", False) else "needs_review",
        "size_chars": len(state.get("doc_content", "")),
    }

    state["doc_metadata"] = metadata
    append_trace(state, "doc_metadata_tagger",
                 f"Tagged: {doc_name} V1.0 ({metadata['size_chars']} chars)")
    return state
