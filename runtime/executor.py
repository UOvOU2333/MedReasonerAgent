from __future__ import annotations

from collections.abc import Callable
from typing import Any

from runtime.decision_policy import decision_policy
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
        start_decision = decision_policy.start_decision(node_name, state)
        self.bus.emit(
            {
                "event": "node_start",
                "node": node_name,
                "decision_id": start_decision.decision_id,
                "parent_decision_id": start_decision.parent_decision_id,
                "available_tools": start_decision.options,
                "decision_options": start_decision.options,
                "state": snapshot_state(state),
            }
        )
        result = node_fn(state)
        end_decision = decision_policy.end_decision(node_name, result)
        self.bus.emit(
            {
                "event": "node_end",
                "node": node_name,
                "decision_id": end_decision.decision_id,
                "parent_decision_id": end_decision.parent_decision_id,
                "available_tools": end_decision.options,
                "decision_options": end_decision.options,
                "selected_tool": end_decision.selected_option,
                "selected_option": end_decision.selected_option,
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
    """Create a lightweight state snapshot, excluding large internal fields."""
    snapshot: dict[str, Any] = {}
    for key, value in state.items():
        if key == "trace":
            continue
        if isinstance(value, (str, int, float, bool, list, dict)):
            snapshot[key] = value
        else:
            snapshot[key] = str(value)
    return snapshot
