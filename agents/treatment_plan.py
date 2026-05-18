from tools.llm import call_llm
from tools.trace import append_trace

def treatment_plan_agent(state):
    language = "Chinese" if state.get("language") == "zh" else "English"
    prompt = f"""
You are a clinical treatment planning agent.

Medical Report:
{state.get('medical_report')}

Reasoning Paths:
{state.get('ranked_paths')}

Task:
Generate:
1. possible treatment options
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
    }

    state["treatment_plan"] = plan

    append_trace(state, "treatment_plan", plan)

    return state
