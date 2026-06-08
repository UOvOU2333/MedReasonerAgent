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
    # DRG 入组智能体
    "supervisor": None,
    "entity": "supervisor",
    "medical_report": "entity",
    "retrieval": "medical_report",
    "reasoning": "retrieval",
    "ranking": "reasoning",
    "treatment_plan": "ranking",
    "explain": "treatment_plan",

    # 文档自动生成智能体
    "doc_supervisor": None,
    "code_scanner": "doc_supervisor",
    "context_collector": "code_scanner",
    "doc_composer": "context_collector",
    "doc_formatter": "doc_composer",
    "doc_reviewer": "doc_formatter",

    # 虚拟文档系统智能体
    "doc_receiver": None,
    "doc_validator": "doc_receiver",
    "doc_metadata_tagger": "doc_validator",
    "doc_storer": "doc_metadata_tagger",
    "doc_notifier": "doc_storer",
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

        # ── 文档自动生成智能体 ──
        if node_name == "doc_supervisor":
            return ["requirements_router", "architecture_router", "testing_router"]
        if node_name == "code_scanner":
            return ["structure_scanner", "dependency_analyzer", "api_inspector"]
        if node_name == "context_collector":
            return ["readme_parser", "config_extractor", "docstring_collector"]
        if node_name == "doc_composer":
            return ["requirements_composer", "architecture_composer", "testing_composer"]
        if node_name == "doc_formatter":
            return ["markdown_formatter", "table_aligner", "section_numberer"]
        if node_name == "doc_reviewer":
            return ["completeness_checker", "format_validator", "numbering_auditor"]

        # ── 虚拟文档系统智能体 ──
        if node_name == "doc_receiver":
            return ["content_ingestor", "format_detector", "source_tagger"]
        if node_name == "doc_validator":
            return ["structure_validator", "section_counter", "metadata_checker"]
        if node_name == "doc_metadata_tagger":
            return ["version_tagger", "date_stamper", "author_recorder"]
        if node_name == "doc_storer":
            return ["filesystem_writer", "backup_handler", "path_resolver"]
        if node_name == "doc_notifier":
            return ["index_updater", "event_emitter", "log_recorder"]
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

        # ── 文档自动生成智能体 ──
        if node_name == "doc_supervisor":
            doc_type = str(state.get("doc_type", "")).lower()
            if "architecture" in doc_type or "架构" in doc_type:
                return "architecture_router"
            if "testing" in doc_type or "test" in doc_type or "测试" in doc_type:
                return "testing_router"
            return "requirements_router"
        if node_name == "code_scanner":
            return "structure_scanner"
        if node_name == "context_collector":
            return "readme_parser"
        if node_name == "doc_composer":
            doc_type = str(state.get("doc_type", "")).lower()
            if "architecture" in doc_type or "架构" in doc_type:
                return "architecture_composer"
            if "testing" in doc_type or "test" in doc_type or "测试" in doc_type:
                return "testing_composer"
            return "requirements_composer"
        if node_name == "doc_formatter":
            return "markdown_formatter"
        if node_name == "doc_reviewer":
            return "completeness_checker"

        # ── 虚拟文档系统智能体 ──
        if node_name == "doc_receiver":
            return "content_ingestor"
        if node_name == "doc_validator":
            return "structure_validator"
        if node_name == "doc_metadata_tagger":
            return "version_tagger"
        if node_name == "doc_storer":
            return "filesystem_writer"
        if node_name == "doc_notifier":
            return "index_updater"

        return options[0]


def reasoning_options() -> list[str]:
    options = ["llm_reasoner"]
    if os.getenv("OPENAI_MODEL", "").startswith("deepseek"):
        options.append("deepseek_reasoner")
    if os.getenv("SGLANG_BASE_URL"):
        options.append("sglang_reasoner")
    return options


decision_policy = DecisionPolicy()
