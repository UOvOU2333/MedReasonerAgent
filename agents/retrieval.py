from kg.query import get_subgraph
from tools.trace import append_trace

def retrieval_agent(state):
    subgraph = get_subgraph(state["entities"], hops=2)

    state["subgraph"] = subgraph

    append_trace(state, "retrieval", f"{len(subgraph.get('edges', []))} edges")

    return state
