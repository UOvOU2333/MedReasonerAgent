from tools.llm import call_llm

def medical_report_agent(state):
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

Return structured JSON.
"""

    result = call_llm(prompt)

    report = {
        "raw": result
    }

    state["medical_report"] = report

    state["trace"].append({
        "node": "medical_report_agent",
        "output": report
    })

    return state