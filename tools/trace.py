from __future__ import annotations

from typing import Any


def append_trace(state: dict[str, Any], node: str, output: Any) -> dict[str, Any]:
    state.setdefault("trace", []).append({"node": node, "output": output})
    return state
