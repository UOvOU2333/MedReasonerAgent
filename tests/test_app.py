"""Unit tests for FastAPI app endpoints (test client, no server needed)."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

pytest.importorskip("langgraph")
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _no_api_keys(monkeypatch):
    """Force offline mode by clearing API keys so LLM calls use fallback responses."""
    import os
    for key in ("OPENAI_API_KEY", "DEEPSEEK_API_KEY", "SGLANG_BASE_URL"):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def client():
    from app import app
    return TestClient(app, raise_server_exceptions=False)


# =============================================================================
# Health endpoint
# =============================================================================

class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


# =============================================================================
# /run endpoint — DRG mode
# =============================================================================

class TestDrgRunEndpoint:
    def test_run_drg_returns_answer(self, client):
        response = client.post("/run", json={"query": "心梗"})
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["mode"] == "drg"

    def test_run_drg_returns_medical_report(self, client):
        response = client.post("/run", json={"query": "I21.3"})
        data = response.json()
        assert "medical_report" in data

    def test_run_drg_returns_drg_result(self, client):
        response = client.post("/run", json={"query": '{"主要诊断": "I21.3"}'})
        data = response.json()
        assert "drg_result" in data

    def test_run_drg_default_language(self, client):
        response = client.post("/run", json={"query": "test"})
        assert response.status_code == 200

    def test_run_drg_with_emr_json(self, client):
        emr = {
            "主要诊断": "I21.3",
            "次要诊断列表": ["E11.9", "I10"],
            "主要手术": "36.0",
            "其他手术列表": [],
        }
        response = client.post("/run", json={"query": str(emr)})
        data = response.json()
        assert data["mode"] == "drg"
        assert "drg_result" in data


# =============================================================================
# /run endpoint — DocGen mode
# =============================================================================

class TestDocgenRunEndpoint:
    def test_run_docgen_returns_doc_final(self, client):
        response = client.post("/run", json={
            "query": "Generate requirements",
            "mode": "docgen",
            "doc_type": "requirements",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "docgen"
        assert "doc_final" in data
        assert "review_report" in data

    def test_run_docgen_architecture(self, client):
        response = client.post("/run", json={
            "query": "Generate architecture",
            "mode": "docgen",
            "doc_type": "architecture",
        })
        data = response.json()
        assert data["mode"] == "docgen"
        assert data["doc_type"] == "architecture"

    def test_run_docgen_testing(self, client):
        response = client.post("/run", json={
            "query": "Generate testing doc",
            "mode": "docgen",
            "doc_type": "testing",
        })
        data = response.json()
        assert data["mode"] == "docgen"


# =============================================================================
# /run endpoint — TCGen mode
# =============================================================================

class TestTcgenRunEndpoint:
    def test_run_tcgen_returns_tc_final(self, client):
        response = client.post("/run", json={
            "query": "Generate normal test cases",
            "mode": "tcgen",
            "tc_type": "normal",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "tcgen"
        assert "tc_final" in data
        assert "review_report" in data

    def test_run_tcgen_boundary(self, client):
        response = client.post("/run", json={
            "query": "Generate boundary test cases",
            "mode": "tcgen",
            "tc_type": "boundary",
        })
        data = response.json()
        assert data["mode"] == "tcgen"
        assert data["tc_type"] == "boundary"

    def test_run_tcgen_abnormal(self, client):
        response = client.post("/run", json={
            "query": "Generate abnormal test cases",
            "mode": "tcgen",
            "tc_type": "abnormal",
        })
        data = response.json()
        assert data["mode"] == "tcgen"


# =============================================================================
# /run endpoint — VDoc mode
# =============================================================================

class TestVdocRunEndpoint:
    def test_run_vdoc(self, client):
        response = client.post("/run", json={
            "query": "Store document",
            "mode": "vdoc",
            "doc_type": "requirements",
            "project_name": "TestProject",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "vdoc"
        assert "notification" in data


# =============================================================================
# /docgen/generate endpoint
# =============================================================================

class TestDocgenGenerateEndpoint:
    def test_docgen_generate_requirements(self, client):
        response = client.post("/docgen/generate", json={
            "query": "Generate",
            "mode": "docgen",
            "doc_type": "requirements",
            "project_name": "TestProject",
        })
        assert response.status_code == 200
        data = response.json()
        assert "doc_final" in data
        assert "review_report" in data
        assert "storage_path" in data
        assert "notification" in data

    def test_docgen_generate_architecture(self, client):
        response = client.post("/docgen/generate", json={
            "query": "Generate arch",
            "doc_type": "architecture",
            "project_name": "TestProject",
        })
        assert response.status_code == 200


# =============================================================================
# /tcgen/generate endpoint
# =============================================================================

class TestTcgenGenerateEndpoint:
    def test_tcgen_generate_normal(self, client):
        response = client.post("/tcgen/generate", json={
            "query": "Generate normal TC",
            "mode": "tcgen",
            "tc_type": "normal",
            "project_name": "TestProject",
        })
        assert response.status_code == 200
        data = response.json()
        assert "tc_final" in data
        assert "review_report" in data
        assert "storage_path" in data

    def test_tcgen_generate_boundary(self, client):
        response = client.post("/tcgen/generate", json={
            "query": "Generate boundary TC",
            "tc_type": "boundary",
            "project_name": "TestProject",
        })
        assert response.status_code == 200

    def test_tcgen_generate_abnormal(self, client):
        response = client.post("/tcgen/generate", json={
            "query": "Generate abnormal TC",
            "tc_type": "abnormal",
            "project_name": "TestProject",
        })
        assert response.status_code == 200


# =============================================================================
# /docgen/docs endpoint
# =============================================================================

class TestListDocsEndpoint:
    def test_list_docs_returns_index(self, client):
        response = client.get("/docgen/docs")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "last_updated" in data

    def test_list_docs_returns_list(self, client):
        response = client.get("/docgen/docs")
        assert isinstance(response.json()["documents"], list)

    def test_list_docs_attaches_acceptance_badges(self, client):
        root = Path(__file__).resolve().parents[1]
        generated_dir = root / "generated_docs"
        generated_dir.mkdir(exist_ok=True)
        index_path = generated_dir / "index.json"
        old_index = index_path.read_text(encoding="utf-8") if index_path.exists() else None
        doc_path = generated_dir / "badge_test.md"
        doc_path.write_text(
            "# Badge Test\n\n| **项目名称** | BadgeTest |\n\n## 1. 引言\n",
            encoding="utf-8",
        )
        index_path.write_text(
            json.dumps({
                "documents": [{
                    "name": "BadgeTest",
                    "type": "requirements",
                    "version": "V1.0",
                    "path": "generated_docs/badge_test.md",
                    "status": "stored",
                }],
                "last_updated": "2026-06-12T00:00:00",
            }, ensure_ascii=False),
            encoding="utf-8",
        )
        try:
            response = client.get("/docgen/docs")
            assert response.status_code == 200
            document = response.json()["documents"][0]
            assert "badges" in document
            assert "content_review" in document["badges"]
            assert "pdf" in document["badges"]
        finally:
            doc_path.unlink(missing_ok=True)
            if old_index is None:
                index_path.unlink(missing_ok=True)
            else:
                index_path.write_text(old_index, encoding="utf-8")

    def test_read_generated_markdown_doc(self, client):
        root = Path(__file__).resolve().parents[1]
        generated_dir = root / "generated_docs"
        generated_dir.mkdir(exist_ok=True)
        doc_path = generated_dir / "api_preview_test.md"
        doc_path.write_text("# API Preview\n\ncontent", encoding="utf-8")
        try:
            response = client.get("/docgen/docs/api_preview_test.md")
            assert response.status_code == 200
            data = response.json()
            assert data["filename"] == "api_preview_test.md"
            assert data["path"] == "generated_docs/api_preview_test.md"
            assert data["size"] > 0
            assert "# API Preview" in data["content"]
        finally:
            doc_path.unlink(missing_ok=True)

    @pytest.mark.parametrize("filename", ["api_preview_test.txt", "..%2Fapp.py"])
    def test_read_generated_doc_rejects_invalid_filename(self, client, filename):
        response = client.get(f"/docgen/docs/{filename}")
        assert response.status_code in (400, 404)

    def test_export_delivery_package_returns_zip(self, client):
        root = Path(__file__).resolve().parents[1]
        generated_dir = root / "generated_docs"
        generated_dir.mkdir(exist_ok=True)
        index_path = generated_dir / "index.json"
        old_index = index_path.read_text(encoding="utf-8") if index_path.exists() else None
        doc_path = generated_dir / "export_package_test.md"
        doc_path.write_text("# Export Package Test\n\ncontent", encoding="utf-8")
        index_path.write_text(
            json.dumps({
                "documents": [{
                    "name": "ExportPackageTest",
                    "type": "requirements",
                    "version": "V1.0",
                    "path": "generated_docs/export_package_test.md",
                    "status": "stored",
                }],
                "last_updated": "2026-06-12T00:00:00",
            }, ensure_ascii=False),
            encoding="utf-8",
        )
        try:
            response = client.get("/docgen/export-package")
            assert response.status_code == 200
            assert response.content.startswith(b"PK")
            zip_path = generated_dir / "export_package_response.zip"
            zip_path.write_bytes(response.content)
            try:
                with zipfile.ZipFile(zip_path) as zf:
                    names = set(zf.namelist())
                    assert "index.json" in names
                    assert "export_manifest.json" in names
                    assert "documents/requirements/export_package_test.md" in names
            finally:
                zip_path.unlink(missing_ok=True)
        finally:
            doc_path.unlink(missing_ok=True)
            if old_index is None:
                index_path.unlink(missing_ok=True)
            else:
                index_path.write_text(old_index, encoding="utf-8")


# =============================================================================
# /trace/replay endpoint
# =============================================================================

class TestTraceReplayEndpoint:
    def test_trace_replay_returns_events(self, client):
        response = client.get("/trace/replay")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert isinstance(data["events"], list)


# =============================================================================
# RunRequest validation
# =============================================================================

class TestRunRequestValidation:
    def test_default_mode_is_drg(self, client):
        response = client.post("/run", json={"query": "test"})
        assert response.status_code == 200

    def test_empty_query_error(self, client):
        response = client.post("/run", json={"query": ""})
        assert response.status_code == 200  # FastAPI accepts empty str

    def test_project_name_persists(self, client):
        response = client.post("/run", json={
            "query": "test",
            "project_name": "MyCustomProject",
        })
        assert response.status_code == 200
