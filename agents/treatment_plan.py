from tools.llm import call_llm

def treatment_plan_agent(state):
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

Return structured JSON.
"""

    result = call_llm(prompt)

    plan = {
        "raw": result
    }

    state["treatment_plan"] = plan

    state["trace"].append({
        "node": "treatment_plan_agent",
        "output": plan
    })

    return state