from tools.llm import call_llm
from tools.trace import append_trace


def entity_agent(state):
    language = "Chinese" if state.get("language") == "zh" else "English"
    prompt = f"Extract biomedical entities from this query. Reply in {language}: {state['query']}"
    result = call_llm(prompt)

    entities = [item.strip() for item in result.split(",") if item.strip()]

    state["entities"] = entities

    append_trace(state, "entity", entities)

    return state
