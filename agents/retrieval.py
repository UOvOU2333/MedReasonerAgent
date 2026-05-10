from kg.query import get_subgraph

def retrieval_agent(state):
    subgraph = get_subgraph(state["entities"], hops=2)

    state["subgraph"] = subgraph

    state["trace"].append({
        "node": "retrieval_agent",
        "output": f"{len(subgraph)} edges"
    })

    return state