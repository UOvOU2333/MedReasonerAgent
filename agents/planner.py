from tools.trace import append_trace


def planner_agent(state):
    plan = [
        "entity",
        "medical_report",
        "retrieval",
        "reasoning",
        "ranking",
        "treatment_plan",
        "explain",
    ]
    state["plan"] = {"nodes": plan, "mode": state.get("plan", {}).get("mode", "deep-reasoning")}
    append_trace(state, "planner", state["plan"])
    return state
