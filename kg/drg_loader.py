from __future__ import annotations

from typing import Any


def load_drg_graph() -> list[dict[str, Any]]:
    return [
        {"source": "symptom", "relation": "suggests", "target": "disease"},
        {"source": "disease", "relation": "mapped_to", "target": "drg_group"},
        {"source": "disease", "relation": "treated_by", "target": "treatment"},
        {"source": "risk_factor", "relation": "increases_risk_of", "target": "disease"},
        {"source": "test", "relation": "confirms_or_rules_out", "target": "disease"},
    ]
