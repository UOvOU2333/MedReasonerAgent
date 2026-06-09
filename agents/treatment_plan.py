import json
from tools.llm import call_llm
from tools.trace import append_trace


def treatment_plan_agent(state):
    language = "Chinese" if state.get("language") == "zh" else "English"
    drg = state.get("drg_result", {})

    # 注入 DRG 入组结果上下文
    drg_context = ""
    if drg and drg.get("drg") != "N/A":
        drg_context = f"""
DRG Grouping Result (pre-computed):
- DRG Code: {drg.get('drg', '')}
- DRG Name: {drg.get('drg_name', '')}
- MDC: {drg.get('mdc', '')} ({drg.get('mdc_name', '')})
- ADRG: {drg.get('adrg', '')} ({drg.get('adrg_name', '')})
- Complication Level: {drg.get('complication', 'none')}
- Confidence: {drg.get('confidence', 0):.0%}
"""

    prompt = f"""
You are a clinical treatment planning agent.

{drg_context}

Medical Report:
{state.get('medical_report')}

Reasoning Paths:
{state.get('ranked_paths')}

Task:
Generate:
1. possible treatment options (aligned with the DRG group above)
2. drug candidates (if any)
3. mechanism explanation
4. confidence level
5. warnings / limitations

Return structured JSON in {language}.
"""

    result = call_llm(prompt)
    plan = {
        "text": result,
        "warning": "For clinical decision support only; confirm with licensed professionals.",
        "drg_code": drg.get("drg", "") if drg else "",
    }
    state["treatment_plan"] = plan
    append_trace(state, "treatment_plan", plan)
    return state
