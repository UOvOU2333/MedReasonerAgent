from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Decision:
    decision_id: str
    parent_decision_id: str | None
    options: list[str]
    selected_option: str | None = None


GRAPH_PARENTS: dict[str, str | None] = {
    "supervisor": None,
    "entity": "supervisor",
    "medical_report": "entity",
    "retrieval": "medical_report",
    "reasoning": "retrieval",
    "ranking": "reasoning",
    "treatment_plan": "ranking",
    "explain": "treatment_plan",
}


class DecisionPolicy:
    def start_decision(self, node_name: str, state: dict[str, Any]) -> Decision:
        return Decision(
            decision_id=node_name,
            parent_decision_id=GRAPH_PARENTS.get(node_name),
            options=self._options_for(node_name, state),
        )

    def end_decision(self, node_name: str, state: dict[str, Any]) -> Decision:
        options = self._options_for(node_name, state)
        selected = self._select_option(node_name, state, options)
        return Decision(
            decision_id=node_name,
            parent_decision_id=GRAPH_PARENTS.get(node_name),
            options=options,
            selected_option=selected,
        )

    def _options_for(self, node_name: str, state: dict[str, Any]) -> list[str]:
        if node_name == "supervisor":
            return ["simple", "multi-hop", "deep-reasoning"]
        if node_name == "entity":
            return ["entity_extractor", "terminology_normalizer", "symptom_parser"]
        if node_name == "medical_report":
            return ["case_summarizer", "risk_factor_analyzer", "severity_estimator"]
        if node_name == "retrieval":
            return ["direct_drg_lookup", "multi_hop_expansion", "fallback_subgraph"]
        if node_name == "reasoning":
            return reasoning_options()
        if node_name == "ranking":
            return ["path_ranker", "confidence_scorer", "evidence_filter"]
        if node_name == "treatment_plan":
            return ["treatment_generator", "drug_candidate_lookup", "warning_checker"]
        if node_name == "explain":
            return ["trace_summarizer", "plain_language_explainer", "limitation_writer"]
        return []

    def _select_option(self, node_name: str, state: dict[str, Any], options: list[str]) -> str | None:
        if not options:
            return None
        if node_name == "supervisor":
            plan = str(state.get("plan", {}).get("mode", "")).lower()
            if "deep" in plan:
                return "deep-reasoning"
            if "multi" in plan:
                return "multi-hop"
            return "simple"
        if node_name == "entity":
            entities = state.get("entities", [])
            return "terminology_normalizer" if len(entities) > 5 else "entity_extractor"
        if node_name == "medical_report":
            report = str(state.get("medical_report", {})).lower()
            return "severity_estimator" if "severity" in report else "case_summarizer"
        if node_name == "retrieval":
            edges = state.get("subgraph", {}).get("edges", [])
            return "multi_hop_expansion" if len(edges) > 2 else "direct_drg_lookup"
        if node_name == "reasoning":
            engine = os.getenv("REASONING_ENGINE", "sglang")
            model = os.getenv("OPENAI_MODEL", "")
            if engine == "sglang" and os.getenv("SGLANG_BASE_URL"):
                return "sglang_reasoner"
            if "deepseek" in model:
                return "deepseek_reasoner"
            return "llm_reasoner"
        if node_name == "ranking":
            ranked = state.get("ranked_paths", [])
            return "confidence_scorer" if len(ranked) > 1 else "path_ranker"
        if node_name == "treatment_plan":
            plan = str(state.get("treatment_plan", {})).lower()
            return "warning_checker" if "warning" in plan else "treatment_generator"
        if node_name == "explain":
            return "plain_language_explainer"
        return options[0]


def reasoning_options() -> list[str]:
    options = ["llm_reasoner"]
    if os.getenv("OPENAI_MODEL", "").startswith("deepseek"):
        options.append("deepseek_reasoner")
    if os.getenv("SGLANG_BASE_URL"):
        options.append("sglang_reasoner")
    return options


decision_policy = DecisionPolicy()
