"""Unit tests for tc_reviewer_agent — deterministic test-case quality checks."""
from __future__ import annotations

import pytest
from agents.tc_reviewer import (
    _check_gaps,
    _check_xxx_standalone,
    _extract_numbers,
    _section_exists,
    tc_reviewer_agent,
)


# =============================================================================
# _check_xxx_standalone() tests
# =============================================================================

class TestCheckXxxStandalone:
    def test_standalone_xxx_detected(self):
        doc = "# Test\nSome text XXX here"
        assert _check_xxx_standalone(doc)

    def test_xxx_in_json_code_block_excluded(self):
        doc = "# Test\n```json\n{\"code\": \"XXXX.X\"}\n```\nXXX standalone"
        assert _check_xxx_standalone(doc)

    def test_xxx_in_json_allowed(self):
        doc = "# Test\n```json\n{\"code\": \"XXXX.X\", \"name\": \"test\"}\n```"
        assert not _check_xxx_standalone(doc)

    def test_xxx_in_icd_code_pattern_excluded(self):
        doc = "# Test\nICD code XXXX.X is invalid\nXXX"
        assert _check_xxx_standalone(doc)

    def test_tc_xxx_pattern_allowed(self):
        doc = "# Test\nTC-XXX-01: placeholder case\nXXX"
        assert _check_xxx_standalone(doc)

    def test_clean_doc_no_xxx(self):
        doc = "# Test Cases\n## TC-N-1: Valid case\nValid content."
        assert not _check_xxx_standalone(doc)


# =============================================================================
# _section_exists() tests (same logic as doc_reviewer)
# =============================================================================

class TestSectionExists:
    def test_exact_match(self):
        doc = "## 1. 测试概述\nSome text"
        assert _section_exists(doc, "## 1. 测试概述")

    def test_chinese_number_stripped(self):
        doc = "## 一、测试概述\nSome text"
        assert _section_exists(doc, "## 1. 测试概述")

    def test_no_number(self):
        doc = "## 测试概述\nSome text"
        assert _section_exists(doc, "## 1. 测试概述")


# =============================================================================
# _extract_numbers() and _check_gaps() tests
# =============================================================================

class TestExtractNumbersAndGaps:
    def test_tc_n_extraction(self):
        doc = "TC-N-1 ... TC-N-2 ... TC-N-3"
        assert _extract_numbers(doc, "TC-N-") == [1, 2, 3]

    def test_tc_b_extraction(self):
        doc = "TC-B-1 ... TC-B-7"
        assert _extract_numbers(doc, "TC-B-") == [1, 7]

    def test_tc_a_extraction(self):
        doc = "TC-A-3 TC-A-5 TC-A-1"
        assert _extract_numbers(doc, "TC-A-") == [1, 3, 5]

    def test_gaps_detected(self):
        assert _check_gaps([1, 2, 4, 5], "TC-N-")

    def test_no_gaps(self):
        assert not _check_gaps([1, 2, 3, 4, 5], "TC-N-")


# =============================================================================
# tc_reviewer_agent() integration tests
# =============================================================================

class TestTcReviewerAgent:
    def _run(self, tc_formatted: str, tc_type: str = "normal",
             language: str = "zh") -> dict:
        state = {"tc_formatted": tc_formatted, "tc_type": tc_type,
                 "language": language, "trace": []}
        return tc_reviewer_agent(state)

    # ── CHK-01: Meta table ────────────────────────────────────────
    def test_meta_table_pass(self):
        doc = "| **项目名称** | MedReasonerAgent |\n# 测试用例\n"
        result = self._run(doc)
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-01")
        assert chk["passed"]

    def test_meta_table_fail(self):
        doc = "# 测试用例\n"
        result = self._run(doc)
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-01")
        assert not chk["passed"]

    # ── CHK-02: Required sections (normal) ─────────────────────────
    def test_normal_sections_present(self):
        doc = (
            "| **项目名称** | Test |\n"
            "# 测试用例\n"
            "## 1. 测试概述\n\n## 2. DRG 分组规则摘要\n"
            "## 3. 测试场景设计\n\n## 4. 测试用例\n\n## 5. 测试数据\n"
        )
        result = self._run(doc, tc_type="normal")
        chk = next(c for c in result["review_report"]["checks"]
                   if c["check"] == "CHK-02" and "1. 测试概述" in c["item"])
        assert chk["passed"]

    # ── CHK-04: Number continuity ──────────────────────────────────
    def test_tc_n_continuous(self):
        doc = (
            "| **项目名称** | Test |\n"
            "# 测试\n"
            "## 1. 测试概述\n"
            "TC-N-1: case 1\n"
            "TC-N-2: case 2\n"
            "TC-N-3: case 3\n"
        )
        result = self._run(doc, tc_type="normal")
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-04")
        assert chk["passed"]

    def test_tc_n_gap_detected(self):
        doc = (
            "| **项目名称** | Test |\n"
            "# 测试\n"
            "## 1. 测试概述\n"
            "TC-N-1: case 1\n"
            "TC-N-2: case 2\n"
            "TC-N-4: case 4\n"
        )
        result = self._run(doc, tc_type="normal")
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-04")
        assert not chk["passed"]

    # ── CHK-05: Placeholders ───────────────────────────────────────
    def test_todo_detected(self):
        doc = "| **项目名称** | T |\n# Test\nTODO: write test"
        result = self._run(doc)
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-05")
        assert not chk["passed"]

    def test_xxx_in_json_allowed(self):
        doc = "| **项目名称** | T |\n# Test\n```json\n{\"code\": \"XXXX.X\"}\n```"
        result = self._run(doc)
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-05")
        assert chk["passed"]

    # ── CHK-07: AI declaration ──────────────────────────────────────
    def test_tcgen_declaration_pass(self):
        doc = (
            "| **项目名称** | Test |\n# 测试\n"
            "*本文档由 TCGen Agent 自动生成，状态为草稿，需人工审核确认。*"
        )
        result = self._run(doc)
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-07")
        assert chk["passed"]

    def test_tcgen_declaration_fail(self):
        doc = "| **项目名称** | Test |\n# 测试\n"
        result = self._run(doc)
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-07")
        assert not chk["passed"]

    # ── CHK-08: JSON block count ───────────────────────────────────
    def test_enough_json_blocks(self):
        doc = "| **项目名称** | T |\n# Test\n" + ("\n```json\n{}\n```\n" * 6)
        result = self._run(doc, tc_type="normal")
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-08")
        assert chk["passed"]

    def test_too_few_json_blocks(self):
        doc = "| **项目名称** | T |\n# Test\n```json\n{}\n```\n" * 2
        result = self._run(doc, tc_type="normal")
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-08")
        assert not chk["passed"]

    # ── CHK-09: Test case count ─────────────────────────────────────
    def test_enough_tc_cases(self):
        doc = (
            "| **项目名称** | T |\n# Test\n"
            + "\n".join(f"TC-N-{i}: case {i}" for i in range(1, 8))
        )
        result = self._run(doc, tc_type="normal")
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-09")
        assert chk["passed"]

    def test_too_few_tc_cases(self):
        doc = "| **项目名称** | T |\n# Test\nTC-N-1: case 1\nTC-N-2: case 2"
        result = self._run(doc, tc_type="normal")
        chk = next(c for c in result["review_report"]["checks"] if c["check"] == "CHK-09")
        assert not chk["passed"]

    # ── Overall ──────────────────────────────────────────────────────
    def test_all_pass(self):
        doc = (
            "| **项目名称** | Test |\n"
            "# 测试用例文档\n"
            "## 1. 测试概述\n\n## 2. DRG 分组规则摘要\n"
            "## 3. 测试场景设计\n\n## 4. 测试用例\n\n## 5. 测试数据\n"
            + "\n".join(f"TC-N-{i}: case {i}" for i in range(1, 8))
            + "\n" + "\n```json\n{}\n```\n" * 6
            + "\n*本文档由 TCGen Agent 自动生成，状态为草稿，需人工审核确认。*"
        )
        result = self._run(doc, tc_type="normal")
        assert result["review_report"]["passed"]

    def test_state_returned(self):
        state = {"tc_formatted": "| **项目名称** | T |\n# Test\n", "tc_type": "normal",
                 "language": "zh", "trace": []}
        result = tc_reviewer_agent(state)
        assert "tc_final" in result
        assert "review_report" in result
