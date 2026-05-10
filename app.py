from fastapi import FastAPI
from graph.workflow import build_graph

app = FastAPI()
graph = build_graph()

@app.post("/run")
def run(query: str):

    state = {
        "query": query,
        "trace": []
    }

    result = graph.invoke(state)

    return {
        "answer": result["answer"],
        "trace": result["trace"]
    }