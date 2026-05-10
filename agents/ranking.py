def ranking_agent(state):
    paths = state["reasoning_paths"]

    # simple scoring placeholder
    ranked = sorted(paths)

    state["ranked_paths"] = ranked

    state["trace"].append({
        "node": "ranking_agent",
        "output": ranked[:2]
    })

    return state