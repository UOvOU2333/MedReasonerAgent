"""Unit tests for VDoc agents — doc_validator, doc_formatter, doc_storer."""
from __future__ import annotations

import os
import tempfile
from unittest.mock import patch

import pytest

from agents.doc_validator import doc_validator_agent


# =============================================================================
# doc_validator_agent tests
# =============================================================================

class TestDocValidatorAgent:
    def _run(self, doc_content: str, doc_type: str = "requirements") -> dict:
        state = {"doc_content": doc_content, "doc_type": doc_type, "trace": []}
        return doc_validator_agent(state)

    # ── has_title ─────────────────────────────────────────────────
    def test_has_title_pass(self):
        doc = "# Medical Report\nSome content"
        result = self._run(doc)
        chk = next(c for c in result["validation_result"]["checks"] if c["item"] == "has_title")
        assert chk["passed"]

    def test_no_title_fail(self):
        doc = "No markdown heading here"
        result = self._run(doc)
        chk = next(c for c in result["validation_result"]["checks"] if c["item"] == "has_title")
        assert not chk["passed"]

    # ── min_length ────────────────────────────────────────────────
    def test_min_length_pass(self):
        doc = "# Title\n" + "x" * 200
        result = self._run(doc)
        chk = next(c for c in result["validation_result"]["checks"] if c["item"] == "min_length")
        assert chk["passed"]

    def test_min_length_fail(self):
        doc = "# Title\nshort"
        result = self._run(doc)
        chk = next(c for c in result["validation_result"]["checks"] if c["item"] == "min_length")
        assert not chk["passed"]

    # ── has_table ─────────────────────────────────────────────────
    def test_table_present(self):
        doc = "# Title\n| col1 | col2 |\n|------|------|\n| v1 | v2 |"
        result = self._run(doc)
        chk = next(c for c in result["validation_result"]["checks"] if c["item"] == "has_table")
        assert chk["passed"]

    def test_table_missing(self):
        doc = "# Title\nNo table here"
        result = self._run(doc)
        chk = next(c for c in result["validation_result"]["checks"] if c["item"] == "has_table")
        assert not chk["passed"]

    # ── has_structure ──────────────────────────────────────────────
    def test_sufficient_h2_count(self):
        doc = "# Title\n" + "\n".join(f"## Section {i}\n" for i in range(4))
        result = self._run(doc)
        chk = next(c for c in result["validation_result"]["checks"] if c["item"] == "has_structure")
        assert chk["passed"]

    def test_insufficient_h2_count(self):
        doc = "# Title\n## Section 1\n## Section 2\n"
        result = self._run(doc)
        chk = next(c for c in result["validation_result"]["checks"] if c["item"] == "has_structure")
        assert not chk["passed"]

    # ── has_ai_declaration ────────────────────────────────────────
    def test_declaration_present(self):
        doc = "# Title\n自动生成 by AI"
        result = self._run(doc)
        chk = next(c for c in result["validation_result"]["checks"] if c["item"] == "has_ai_declaration")
        assert chk["passed"]

    def test_declaration_english(self):
        doc = "# Title\nautomatically generated"
        result = self._run(doc)
        chk = next(c for c in result["validation_result"]["checks"] if c["item"] == "has_ai_declaration")
        assert chk["passed"]

    def test_declaration_missing(self):
        doc = "# Title\nNo declaration"
        result = self._run(doc)
        chk = next(c for c in result["validation_result"]["checks"] if c["item"] == "has_ai_declaration")
        assert not chk["passed"]

    # ── Overall validation ────────────────────────────────────────
    def test_valid_when_three_checks_pass(self):
        doc = "# Title\n" + "| a | b |\n|--|--|\n" + "## sec1\n## sec2\n## sec3\n" + "x" * 200 + "\n自动生成"
        result = self._run(doc)
        assert result["validation_result"]["valid"]

    def test_invalid_when_only_two_pass(self):
        doc = "# Title\n" + "| a |\n|--|\n" + "## s1\n" + "x" * 50
        result = self._run(doc)
        assert not result["validation_result"]["valid"]

    def test_state_updated(self):
        state = {"doc_content": "# Title\n" + "| a |\n|--|\n" + "## s1\n" * 3 + "x" * 200, "doc_type": "req", "trace": []}
        result = doc_validator_agent(state)
        assert "validation_result" in result
        assert result["validation_result"]["total_count"] == 5
