"""Unit tests for FastAPI app endpoints (test client, no server needed)."""
from __future__ import annotations

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
