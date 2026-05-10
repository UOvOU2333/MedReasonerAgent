from __future__ import annotations

from typing import Any

from kg.drg_loader import load_drg_graph


def get_subgraph(entities: list[str], hops: int = 2) -> dict[str, Any]:
    normalized = {entity.strip().lower() for entity in entities if entity.strip()}
    edges = []
    for edge in load_drg_graph():
        values = {edge["source"].lower(), edge["target"].lower()}
        if normalized & values or not normalized:
            edges.append(edge)

    if not edges:
        edges = load_drg_graph()[: min(hops + 1, len(load_drg_graph()))]

    nodes = sorted({edge["source"] for edge in edges} | {edge["target"] for edge in edges})
    return {"nodes": nodes, "edges": edges, "hops": hops}
