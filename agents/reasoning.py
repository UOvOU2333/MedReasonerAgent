from runtime.router import router
from tools.trace import append_trace


def reasoning_agent(state):
    prompt = f"""
Biomedical reasoning:

Entities: {state['entities']}
Graph: {state['subgraph']}

Task:
- find multi-hop biological reasoning paths
- explain mechanism
"""

    result = router.reason(prompt)

    state["reasoning_paths"] = [result]

    append_trace(state, "reasoning", result)

    return state
