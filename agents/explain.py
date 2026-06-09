from tools.llm import call_llm
from tools.trace import append_trace


def explain_agent(state):
    """
    解释生成 Agent：
    - EMR 模式：生成 Markdown 格式的结构化 DRG 入组结果表
    - NLP 模式：调用 LLM 做自由解释
    """
    drg_result = state.get("drg_result", {})

    # 严格检查：必须有有效的 DRG 编码才走结构化输出
    drg_code = drg_result.get("drg", "") if isinstance(drg_result, dict) else ""
    if drg_code and drg_code not in ("N/A", "none", "unknown", ""):
        answer = _format_drg_result(drg_result, state.get("language", "zh"))
        state["answer"] = answer
        append_trace(state, "explain", f"DRG structured: {drg_code} (confidence: {drg_result.get('confidence', 0):.0%})")
        return state

    # NLP 模式：LLM 自由解释
    language = "Chinese" if state.get("language") == "zh" else "English"
    prompt = f"""
Explain the biomedical reasoning:

Ranked paths:
{state['ranked_paths']}

Medical report:
{state.get('medical_report')}

Treatment plan:
{state.get('treatment_plan')}

Reply in {language}. Use user-friendly language and include medical limitations.
"""
    answer = call_llm(prompt)
    state["answer"] = answer
    append_trace(state, "explain", answer)
    return state


def _format_drg_result(r: dict, lang: str) -> str:
    """将 DRG 入组结果格式化为 Markdown 表格。"""
    is_zh = lang == "zh"

    # 置信度进度条
    confidence = r.get("confidence", 0)
    bar_len = 10
    filled = int(confidence * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)

    # 并发症详情
    comp = r.get("complication", "none")
    comp_zh = {"MCC": "严重合并症/并发症 (MCC)", "CC": "一般合并症/并发症 (CC)", "none": "无合并症/并发症"}
    comp_label = comp_zh.get(comp, comp) if is_zh else comp

    # 入组路径
    steps = r.get("reasoning_steps", [])
    steps_text = "\n".join(f"> {i+1}. {s}" for i, s in enumerate(steps))

    if is_zh:
        return f"""## DRG 入组结果

| 属性 | 内容 |
|------|------|
| **DRG 编码** | **`{r['drg']}`** |
| **DRG 名称** | {r.get('drg_name', '')} |
| **MDC** | {r.get('mdc', '')}（{r.get('mdc_name', '')}） |
| **ADRG** | {r.get('adrg', '')}（{r.get('adrg_name', '')}） |
| **并发症等级** | {comp_label} |
| **置信度** | {confidence:.0%}  `{bar}` |

### 入组路径

{steps_text}

---

> ⚠️ {r.get('warning', 'AI-assisted DRG grouping; for clinical decision support only.')}"""

    else:
        return f"""## DRG Grouping Result

| Property | Value |
|----------|-------|
| **DRG Code** | **`{r['drg']}`** |
| **DRG Name** | {r.get('drg_name', '')} |
| **MDC** | {r.get('mdc', '')} ({r.get('mdc_name', '')}) |
| **ADRG** | {r.get('adrg', '')} ({r.get('adrg_name', '')}) |
| **Complication** | {comp_label} |
| **Confidence** | {confidence:.0%}  `{bar}` |

### Grouping Path

{steps_text}

---

> ⚠️ {r.get('warning', 'AI-assisted DRG grouping; for clinical decision support only.')}"""
