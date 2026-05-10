def entity_agent(state):
    prompt = f"Extract biomedical entities: {state['query']}"
    result = call_llm(prompt)

    entities = result.split(",")

    state["entities"] = entities

    state["trace"].append({
        "node": "entity_agent",
        "output": entities
    })

    return state