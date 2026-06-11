from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agents.entity import _parse_emr
from agents.retrieval import _do_drg_grouping


ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def client():
    from app import app

    return TestClient(app, raise_server_exceptions=False)


def test_standard_drg_cases_match_expected():
    cases = json.loads((ROOT / "test_examples" / "drg_standard_cases.json").read_text(encoding="utf-8"))
    assert len(cases) == 9
    assert {case["category"] for case in cases} == {"normal", "boundary", "abnormal"}

    for case in cases:
        parsed = _parse_emr(json.dumps(case["input_emr"], ensure_ascii=False))
        assert parsed, case["id"]
        actual = _do_drg_grouping(parsed)
        for key in ("mdc", "adrg", "drg", "complication"):
            assert str(actual.get(key)).lower() == str(case["expected"][key]).lower(), case["id"]


def test_docgen_render_endpoint_creates_pdf(client):
    response = client.post(
        "/docgen/render",
        json={"content": "# 验收文档\n\n| 属性 | 内容 |\n|---|---|\n| 项目 | MedReasonerAgent |", "output_name": "acceptance"},
    )
    assert response.status_code == 200
    data = response.json()
    pdf_path = ROOT / data["pdf_path"]
    assert pdf_path.exists()
    assert data["pdf_url"].endswith(f"/{data['filename']}")

    pdf_response = client.get(data["pdf_url"])
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"].startswith("application/pdf")


def test_replay_doc_endpoint_replays_json_cases(client):
    case = json.loads((ROOT / "test_examples" / "drg_standard_cases.json").read_text(encoding="utf-8"))[0]
    replay_doc = ROOT / "generated_docs" / "test_replay_doc.md"
    replay_doc.parent.mkdir(exist_ok=True)
    payload = dict(case["input_emr"])
    payload["expected"] = case["expected"]
    replay_doc.write_text(
        "# 回放测试\n\n```json\n" + json.dumps(payload, ensure_ascii=False, indent=2) + "\n```\n",
        encoding="utf-8",
    )

    response = client.post("/testing/replay-doc", json={"storage_path": "generated_docs/test_replay_doc.md"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["passed"] == 1
    assert data["cases"][0]["actual"]["drg"] == case["expected"]["drg"]


def test_replay_doc_reports_invalid_json(client):
    replay_doc = ROOT / "generated_docs" / "test_replay_invalid.md"
    replay_doc.parent.mkdir(exist_ok=True)
    replay_doc.write_text("# 回放测试\n\n```json\n{\"主要诊断\": \n```\n", encoding="utf-8")

    response = client.post("/testing/replay-doc", json={"storage_path": "generated_docs/test_replay_invalid.md"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["failed"] == 1
    assert "JSON parse error" in data["cases"][0]["error"]
