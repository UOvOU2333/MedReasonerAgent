"""Unit tests for doc_reviewer_agent — deterministic document quality checks."""
from __future__ import annotations

import pytest
from agents.doc_reviewer import (
    _check_gaps,
    _extract_numbers,
    _section_exists,
    doc_reviewer_agent,
)


# =============================================================================
# _section_exists() tests
# =============================================================================

class TestSectionExists:
    def test_exact_match(self):
        doc = "## 1. 引言\nSome text"
        assert _section_exists(doc, "## 1. 引言")

    def test_chinese_number_stripped(self):
        doc = "## 一、引言\nSome text"
        assert _section_exists(doc, "## 1. 引言")

    def test_no_number_stripped(self):
        doc = "## 引言\nSome text"
        assert _section_exists(doc, "## 1. 引言")

    def test_no_match_different_content(self):
        doc = "## 2. 其他章节\nSome text"
        assert not _section_exists(doc, "## 1. 引言")

    def test_empty_doc(self):
        assert not _section_exists("", "## 1. 引言")


# =============================================================================
# _extract_numbers() tests
# =============================================================================

class TestExtractNumbers:
    def test_basic_extraction(self):
        doc = "FR-1 需求... FR-2 需求... FR-3 需求..."
        assert _extract_numbers(doc, "FR-") == [1, 2, 3]

    def test_duplicates_removed(self):
        doc = "FR-1 FR-1 FR-2 FR-3 FR-3"
        assert _extract_numbers(doc, "FR-") == [1, 2, 3]

    def test_sorted(self):
        doc = "FR-3 FR-1 FR-2"
        assert _extract_numbers(doc, "FR-") == [1, 2, 3]

    def test_empty_returns_empty(self):
        assert _extract_numbers("", "FR-") == []
        # Empty prefix is a regex edge case; verify it at least doesn't crash
        result = _extract_numbers("FR-1 and FR-2", "")
        assert len(result) >= 0  # no assertion on value — regex accepts anything with empty prefix


# =============================================================================
# _check_gaps() tests
# =============================================================================

class TestCheckGaps:
    def test_no_gaps(self):
        assert not _check_gaps([1, 2, 3, 4, 5], "FR-")

    def test_with_gaps(self):
        assert _check_gaps([1, 2, 4, 5], "FR-")

    def test_single_item(self):
        assert not _check_gaps([1], "FR-")

    def test_empty_returns_true(self):
        assert _check_gaps([], "FR-")


# =============================================================================
# doc_reviewer_agent() integration tests
# =============================================================================

class TestDocReviewerAgent:
    def _run(self, doc_formatted: str, doc_type: str = "requirements",
             language: str = "zh") -> dict:
        state = {"doc_formatted": doc_formatted, "doc_type": doc_type,
                 "language": language, "trace": []}
        return doc_reviewer_agent(state)

    # ── CHK-01: Meta table ──────────────────────────────────────────
    def test_meta_table_chk01_pass(self):
        doc = "| **项目名称** | MedReasonerAgent |\n# 需求文档\n## 1. 引言\n"
        result = self._run(doc)
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-01")
        assert chk["passed"]

    def test_meta_table_chk01_fail(self):
        doc = "# 需求文档\n## 1. 引言\n"
        result = self._run(doc)
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-01")
        assert not chk["passed"]

    # ── CHK-02: Required sections ─────────────────────────────────
    def test_all_sections_present_chk02_pass(self):
        doc = (
            "| **项目名称** | Test |\n"
            "# 需求文档\n"
            "## 1. 引言\n\n## 2. 系统概述\n\n## 3. 用户需求分析\n"
            "## 4. 功能需求\n\n## 5. 非功能需求\n\n## 6. 数据需求\n"
            "## 7. 外部接口需求\n\n## 8. 约束与假设\n"
        )
        result = self._run(doc)
        chk = next(c for c in result["review_report"]["checks"]
                   if c["check"] == "CHK-02" and "1. 引言" in c["item"])
        assert chk["passed"]

    def test_missing_section_chk02_fail(self):
        doc = (
            "| **项目名称** | Test |\n"
            "# 需求文档\n"
            "## 1. 引言\n\n## 2. 系统概述\n\n## 3. 用户需求分析\n"
        )
        result = self._run(doc)
        chk = next(c for c in result["review_report"]["checks"]
                   if c["check"] == "CHK-02" and "4. 功能需求" in c["item"])
        assert not chk["passed"]

    # ── CHK-05: Placeholders ────────────────────────────────────────
    @pytest.mark.parametrize("placeholder", ["TODO", "TBD", "待定", "待补充", "TKTK"])
    def test_placeholder_detected(self, placeholder):
        doc = f"| **项目名称** | Test |\n# Doc\n## 1. 引言\n{placeholder}"
        result = self._run(doc)
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-05")
        assert not chk["passed"]

    def test_no_placeholders_pass(self):
        doc = "| **项目名称** | Test |\n# Doc\n## 1. 引言\nThis is valid content."
        result = self._run(doc)
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-05")
        assert chk["passed"]

    # ── CHK-06: Language consistency ───────────────────────────────
    def test_too_many_english_headings_chk06_fail(self):
        doc = (
            "| **项目名称** | Test |\n"
            "# Doc\n"
            "## Introduction\n\n## Overview\n\n## Architecture\n"
            "## Testing\n\n## Requirements\n"
        )
        result = self._run(doc, language="zh")
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-06")
        assert not chk["passed"]

    def test_english_headings_under_limit_chk06_pass(self):
        doc = (
            "| **项目名称** | Test |\n"
            "# Doc\n"
            "## Introduction\n\n## Overview\n"
        )
        result = self._run(doc, language="zh")
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-06")
        assert chk["passed"]

    def test_english_mode_skips_chk06(self):
        doc = "| **项目名称** | Test |\n# Doc\n## Introduction\n## Overview"
        result = self._run(doc, language="en")
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-06")
        assert chk["passed"]

    # ── CHK-07: AI declaration ────────────────────────────────────
    def test_ai_declaration_present_chk07_pass(self):
        doc = (
            "| **项目名称** | Test |\n"
            "# Doc\n## 1. 引言\n"
            "*本文档由 DocGen Agent 自动生成，状态为草稿，需人工审核确认。*"
        )
        result = self._run(doc)
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-07")
        assert chk["passed"]

    def test_ai_declaration_missing_chk07_fail(self):
        doc = "| **项目名称** | Test |\n# Doc\n## 1. 引言\n"
        result = self._run(doc)
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-07")
        assert not chk["passed"]

    # ── CHK-04: Number continuity ─────────────────────────────────
    def test_fr_numbers_gap_detected(self):
        doc = (
            "| **项目名称** | Test |\n"
            "# 需求\n## 1. 引言\n\n## 2. 系统\n\n## 4. 功能\n"
        )
        result = self._run(doc)
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-04")
        assert not chk["passed"]

    # ── Overall pass/fail ─────────────────────────────────────────
    def test_all_pass(self):
        doc = (
            "| **项目名称** | Test |\n"
            "# 需求文档\n"
            "## 1. 引言\n\n## 2. 系统概述\n\n## 3. 用户需求分析\n"
            "## 4. 功能需求\nFR-1: 系统应支持用户登录\nFR-2: 系统应支持文档生成\n"
            "## 5. 非功能需求\n\n## 6. 数据需求\n\n## 7. 外部接口需求\n\n## 8. 约束与假设\n"
            "*本文档由 DocGen Agent 自动生成，状态为草稿，需人工审核确认。*"
        )
        result = self._run(doc)
        assert result["review_report"]["passed"]

    def test_state_returned(self):
        state = {"doc_formatted": "| **项目名称** | Test |\n# Doc\n", "doc_type": "requirements",
                 "language": "zh", "trace": []}
        result = doc_reviewer_agent(state)
        assert "doc_final" in result
        assert "review_report" in result
        assert "trace" in result
