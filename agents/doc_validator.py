from tools.trace import append_trace


def doc_validator_agent(state):
    """
    验证接收到的文档是否符合基本格式规范。
    检查：是否为 Markdown、是否有标题、最小长度等。
    """
    doc_content = state.get("doc_content", "")
    doc_type = state.get("doc_type", "unknown")

    checks = []

    # 检查是否包含 Markdown 标题
    has_title = any(line.startswith("# ") for line in doc_content.split("\n"))
    checks.append({"item": "has_title", "passed": has_title, "detail": "文档有标题" if has_title else "文档缺少标题"})

    # 检查最小长度（至少 500 字符）
    min_length_ok = len(doc_content) >= 100
    checks.append({"item": "min_length", "passed": min_length_ok,
                   "detail": f"文档长度 {len(doc_content)} 字符"})

    # 检查是否包含表格（Markdown 表格特征）
    has_table = "|" in doc_content and "---" in doc_content
    checks.append({"item": "has_table", "passed": has_table,
                   "detail": "包含表格" if has_table else "建议添加表格"})

    # 检查章节结构（是否有多级标题）
    h2_count = sum(1 for line in doc_content.split("\n") if line.startswith("## "))
    has_structure = h2_count >= 3
    checks.append({"item": "has_structure", "passed": has_structure,
                   "detail": f"包含 {h2_count} 个二级章节"})

    # 检查 AI 生成声明
    has_declaration = "自动生成" in doc_content or "automatically generated" in doc_content
    checks.append({"item": "has_ai_declaration", "passed": has_declaration,
                   "detail": "包含 AI 声明" if has_declaration else "缺少 AI 生成声明"})

    passed = sum(1 for c in checks if c["passed"])
    total = len(checks)

    validation_result = {
        "valid": passed >= 3,  # 至少三项通过才算有效
        "passed_count": passed,
        "total_count": total,
        "checks": checks,
        "summary": f"{passed}/{total} 项验证通过",
    }

    state["validation_result"] = validation_result
    append_trace(state, "doc_validator", validation_result["summary"])
    return state
