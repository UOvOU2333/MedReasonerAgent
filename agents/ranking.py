from tools.trace import append_trace


def ranking_agent(state):
    paths = state["reasoning_paths"]

    # simple scoring placeholder
    ranked = sorted(paths)

    state["ranked_paths"] = ranked

    append_trace(state, "ranking", ranked[:2])

    return state
