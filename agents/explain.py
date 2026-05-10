def explain_agent(state):
    prompt = f"""
Explain the biomedical reasoning:

{state['ranked_paths']}
"""

    answer = call_llm(prompt)

    state["answer"] = answer

    state["trace"].append({
        "node": "explain_agent",
        "output": answer
    })

    return state