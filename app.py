from __future__ import annotations

import asyncio
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph.workflow import build_graph
from runtime.event_bus import event_bus

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
graph = build_graph()


class RunRequest(BaseModel):
    query: str
    language: str = "zh"


def normalize_language(language: str | None) -> str:
    return "en" if language == "en" else "zh"


def initial_state(query: str, language: str = "zh") -> dict[str, Any]:
    return {
        "query": query,
        "language": normalize_language(language),
        "entities": [],
        "subgraph": {},
        "reasoning_paths": [],
        "ranked_paths": [],
        "medical_report": {},
        "treatment_plan": {},
        "answer": "",
        "plan": {},
        "trace": [],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run")
def run(request: RunRequest):
    result = graph.invoke(initial_state(request.query, request.language))

    return {
        "answer": result["answer"],
        "trace": result["trace"],
        "medical_report": result.get("medical_report", {}),
        "treatment_plan": result.get("treatment_plan", {}),
        "state": result,
    }


@app.get("/trace/replay")
def replay_trace():
    return {"events": event_bus.replay()}


@app.websocket("/ws/run")
async def websocket_run(websocket: WebSocket):
    await websocket.accept()
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    def listener(event: dict[str, Any]) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, event)

    unsubscribe = event_bus.subscribe(listener)
    try:
        payload = await websocket.receive_json()
        query = payload.get("query", "")
        language = normalize_language(payload.get("language"))
        if not query:
            await websocket.send_json({"event": "error", "message": "query is required"})
            return

        task = asyncio.create_task(asyncio.to_thread(graph.invoke, initial_state(query, language)))

        while True:
            if task.done() and queue.empty():
                result = task.result()
                await websocket.send_json(
                    {
                        "event": "complete",
                        "node": "complete",
                        "state": result,
                        "answer": result.get("answer", ""),
                        "trace": result.get("trace", []),
                    }
                )
                break

            try:
                event = await asyncio.wait_for(queue.get(), timeout=0.1)
                await websocket.send_json(event)
            except asyncio.TimeoutError:
                continue

    except WebSocketDisconnect:
        pass
    finally:
        unsubscribe()
