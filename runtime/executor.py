from __future__ import annotations

from collections.abc import Callable
from typing import Any

from runtime.event_bus import EventBus


class Executor:
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus

    def run_node(
        self,
        node_name: str,
        node_fn: Callable[[dict[str, Any]], dict[str, Any]],
        state: dict[str, Any],
    ) -> dict[str, Any]:
        self.bus.emit(
            {
                "event": "node_start",
                "node": node_name,
                "state": snapshot_state(state),
            }
        )
        result = node_fn(state)
        self.bus.emit(
            {
                "event": "node_end",
                "node": node_name,
                "output": latest_node_output(result, node_name),
                "state": snapshot_state(result),
            }
        )
        return result


def latest_node_output(state: dict[str, Any], node_name: str) -> Any:
    for item in reversed(state.get("trace", [])):
        if item.get("node") in {node_name, f"{node_name}_agent"}:
            return item.get("output")
    return None


def snapshot_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "query": state.get("query"),
        "entities": state.get("entities", []),
        "subgraph": state.get("subgraph", {}),
        "reasoning_paths": state.get("reasoning_paths", []),
        "ranked_paths": state.get("ranked_paths", []),
        "medical_report": state.get("medical_report", {}),
        "treatment_plan": state.get("treatment_plan", {}),
        "answer": state.get("answer", ""),
    }
