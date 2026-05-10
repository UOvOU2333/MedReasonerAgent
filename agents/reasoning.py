def reasoning_agent(state):
    prompt = f"""
You are a biomedical reasoning agent.

Entities: {state['entities']}
Graph: {state['subgraph']}

Task:
- find multi-hop biological reasoning paths
- explain mechanism
"""

    result = call_llm(prompt)

    state["reasoning_paths"] = [result]

    state["trace"].append({
        "node": "reasoning_agent",
        "output": result
    })

    return state