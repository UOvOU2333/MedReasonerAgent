from tools.llm import call_llm
from tools.trace import append_trace

def medical_report_agent(state):
    language = "Chinese" if state.get("language") == "zh" else "English"
    prompt = f"""
You are a medical report analysis agent.

User Query:
{state['query']}

Extract structured medical understanding:
- possible disease
- symptoms
- risk factors
- clinical interpretation
- severity estimation

Return structured JSON in {language}.
"""

    result = call_llm(prompt)

    report = {"text": result, "warning": "AI-generated clinical summary for review only."}

    state["medical_report"] = report

    append_trace(state, "medical_report", report)

    return state
