from tools.llm import call_llm
from tools.trace import append_trace


def explain_agent(state):
    prompt = f"""
Explain the biomedical reasoning:

Ranked paths:
{state['ranked_paths']}

Medical report:
{state.get('medical_report')}

Treatment plan:
{state.get('treatment_plan')}
"""

    answer = call_llm(prompt)

    state["answer"] = answer

    append_trace(state, "explain", answer)

    return state
