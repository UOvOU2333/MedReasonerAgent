"""Unit tests for doc_storer_agent — file I/O with tmp directory."""
from __future__ import annotations

import json
import os
import tempfile

import pytest


class TestDocStorerAgent:
    @pytest.fixture(autouse=True)
    def _isolate_storer(self, tmp_path):
        """Replace module-level path constants with a temp directory."""
        import agents.doc_storer as storer
        storer._GENERATED_DIR = str(tmp_path)
        storer._INDEX_FILE = str(tmp_path / "index.json")
        storer._PROJECT_ROOT = str(tmp_path)
        yield
        # Restore defaults
        import agents.doc_storer as storer
        storer._GENERATED_DIR = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "generated_docs",
        )
        storer._INDEX_FILE = os.path.join(storer._GENERATED_DIR, "index.json")
        storer._PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _run(self, doc_content: str, doc_name: str = "TestDoc",
              doc_type: str = "requirements", project_name: str = "TestProject",
              version: str = "V1.0") -> dict:
        from agents.doc_storer import doc_storer_agent
        state = {
            "doc_content": doc_content,
            "doc_metadata": {
                "doc_name": doc_name,
                "doc_type": doc_type,
                "version": version,
            },
            "doc_name": doc_name,
            "doc_type": doc_type,
            "project_name": project_name,
            "trace": [],
        }
        return doc_storer_agent(state)

    def test_file_created(self, tmp_path):
        result = self._run("# Test Content", doc_name="MyDoc")
        assert os.path.exists(tmp_path / "TestProject_requirements_V1.0.md")
        assert result["storage_path"]

    def test_index_updated(self, tmp_path):
        self._run("# Test Content 1", doc_name="Doc1", doc_type="requirements")
        result2 = self._run("# Test Content 2", doc_name="Doc2", doc_type="architecture")

        index_file = tmp_path / "index.json"
        assert index_file.exists()
        index = json.loads(index_file.read_text(encoding="utf-8"))
        assert len(index["documents"]) == 2

    def test_same_doc_version_updates(self, tmp_path):
        """Same name+version should update existing entry."""
        self._run("# Version 1", doc_name="MyDoc", doc_type="requirements")
        result2 = self._run("# Version 2", doc_name="MyDoc", doc_type="requirements")

        index_file = tmp_path / "index.json"
        index = json.loads(index_file.read_text(encoding="utf-8"))
        assert len(index["documents"]) == 1
        assert index["documents"][0]["status"] == "updated"

    def test_state_storage_path_set(self):
        result = self._run("# Content", doc_name="Test")
        assert "storage_path" in result
        assert result["storage_path"].endswith(".md")

    def test_trace_updated(self):
        result = self._run("# Content", doc_name="Test")
        assert len(result["trace"]) >= 1

    def test_corrupted_index_recovered(self, tmp_path):
        """Corrupted index.json should fall back to empty index."""
        index_file = tmp_path / "index.json"
        index_file.write_text("{ invalid json", encoding="utf-8")
        result = self._run("# Content", doc_name="Test")
        assert "storage_path" in result

    def test_state_returned(self):
        state = {
            "doc_content": "# Content",
            "doc_metadata": {"doc_name": "T", "doc_type": "req", "version": "V1.0"},
            "doc_name": "T", "doc_type": "req",
            "project_name": "P", "trace": [],
        }
        from agents.doc_storer import doc_storer_agent
        result = doc_storer_agent(state)
        assert "storage_path" in result
        assert "trace" in result
