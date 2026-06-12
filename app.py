from __future__ import annotations

import asyncio
import json
import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph.workflow import build_graph, build_docgen_graph, build_tcgen_graph, build_vdoc_graph
from runtime.event_bus import event_bus
from agents.entity import _parse_emr
from agents.retrieval import _do_drg_grouping
from agents.doc_reviewer import doc_reviewer_agent
from agents.tc_reviewer import tc_reviewer_agent
from tools.document_renderer import render_markdown_pdf, rendered_pdf_path, resolve_generated_path
from tools.document_replay import compare_drg_result, extract_json_cases

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 四个智能体系统的工作流图
drg_graph = build_graph()
docgen_graph = build_docgen_graph()
tcgen_graph = build_tcgen_graph()
vdoc_graph = build_vdoc_graph()


class RunRequest(BaseModel):
    query: str
    language: str = "zh"
    mode: str = "drg"  # drg | docgen | tcgen | vdoc
    doc_type: str = ""  # requirements | architecture | testing (docgen 专用)
    tc_type: str = ""   # normal | boundary | abnormal (tcgen 专用)
    project_name: str = "MedReasonerAgent"


class RenderRequest(BaseModel):
    storage_path: str = ""
    content: str = ""
    output_name: str = "document"


class ReplayDocRequest(BaseModel):
    storage_path: str


def normalize_language(language: str | None) -> str:
    return "en" if language == "en" else "zh"


# ── DRG 入组智能体初始状态 ──
def drg_initial_state(query: str, language: str = "zh") -> dict[str, Any]:
    return {
        "query": query,
        "language": normalize_language(language),
        "entities": [],
        "subgraph": {},
        "reasoning_paths": [],
        "ranked_paths": [],
        "medical_report": {},
        "treatment_plan": {},
        "emr_data": {},
        "drg_result": {},
        "answer": "",
        "plan": {},
        "trace": [],
    }


# ── 文档自动生成智能体初始状态 ──
def docgen_initial_state(query: str, language: str = "zh",
                         doc_type: str = "", project_name: str = "MedReasonerAgent") -> dict[str, Any]:
    return {
        "query": query,
        "language": normalize_language(language),
        "doc_type": doc_type or "requirements",
        "project_name": project_name,
        "code_analysis": {},
        "context_data": {},
        "doc_draft": "",
        "doc_formatted": "",
        "doc_final": "",
        "review_report": {},
        "answer": "",
        "trace": [],
    }


# ── 测试用例生成智能体初始状态 ──
def tcgen_initial_state(query: str, language: str = "zh",
                         tc_type: str = "", project_name: str = "MedReasonerAgent") -> dict[str, Any]:
    return {
        "query": query,
        "language": normalize_language(language),
        "tc_type": tc_type or "normal",
        "project_name": project_name,
        "drg_rules": {},
        "medical_records": {},
        "tc_draft": "",
        "tc_formatted": "",
        "tc_final": "",
        "review_report": {},
        "answer": "",
        "trace": [],
    }


# ── 虚拟文档系统智能体初始状态 ──
def vdoc_initial_state(query: str, language: str = "zh",
                       doc_name: str = "", doc_content: str = "",
                       doc_type: str = "", project_name: str = "MedReasonerAgent") -> dict[str, Any]:
    return {
        "query": query,
        "language": normalize_language(language),
        "doc_name": doc_name,
        "doc_content": doc_content,
        "doc_type": doc_type or "unknown",
        "project_name": project_name,
        "validation_result": {},
        "doc_metadata": {},
        "storage_path": "",
        "index_status": {},
        "notification": {},
        "answer": "",
        "trace": [],
    }


def select_graph(mode: str):
    """根据 mode 选择对应的 LangGraph 工作流。"""
    if mode == "docgen":
        return docgen_graph
    if mode == "tcgen":
        return tcgen_graph
    if mode == "vdoc":
        return vdoc_graph
    return drg_graph  # 默认 DRG


def select_initial_state(mode: str, request: RunRequest) -> dict[str, Any]:
    """根据 mode 构建对应的初始状态。"""
    if mode == "docgen":
        return docgen_initial_state(
            query=request.query,
            language=request.language,
            doc_type=request.doc_type,
            project_name=request.project_name,
        )
    if mode == "tcgen":
        return tcgen_initial_state(
            query=request.query,
            language=request.language,
            tc_type=request.tc_type,
            project_name=request.project_name,
        )
    if mode == "vdoc":
        return vdoc_initial_state(
            query=request.query,
            language=request.language,
            doc_name=request.project_name or request.query,
            doc_content="",
            doc_type=request.doc_type,
            project_name=request.project_name,
        )
    return drg_initial_state(request.query, request.language)


# ═══════════════════════════════════════════════════
#  API Endpoints
# ═══════════════════════════════════════════════════

# ── 辅助：保存 DRG 入组结果 ──
def _save_drg_result(query: str, drg_graph_result: dict) -> dict:
    """将 DRG 入组结果封装为 JSON 并保存到 results/ 目录。
    返回 {"saved": bool, "path": str, "result": dict}
    """
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)

    # 解析原始输入
    emr_input = {}
    try:
        emr_input = json.loads(query)
    except (json.JSONDecodeError, TypeError):
        return {"saved": False, "path": "", "result": {}}

    if not isinstance(emr_input, dict) or "主要诊断" not in emr_input:
        return {"saved": False, "path": "", "result": {}}

    drg_result = drg_graph_result.get("drg_result", {})

    # 按老师格式构建输出
    output = dict(emr_input)
    output["result"] = {
        "mdc": drg_result.get("mdc", ""),
        "adrg": drg_result.get("adrg", ""),
        "drg": drg_result.get("drg", ""),
        "complication": drg_result.get("complication", ""),
        "confidence": drg_result.get("confidence", 0),
        "reason": drg_result.get("reasoning_steps", []),
    }

    # 写入 timestamp 文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{drg_result.get('drg', 'UNKNOWN')}_{timestamp}.json"
    filepath = os.path.join(results_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return {"saved": True, "path": f"results/{filename}", "result": output}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run")
def run(request: RunRequest):
    mode = request.mode or "drg"
    graph = select_graph(mode)
    state = select_initial_state(mode, request)
    result = graph.invoke(state)

    # 根据 mode 构建不同响应
    base = {
        "answer": result.get("answer", ""),
        "trace": result.get("trace", []),
        "mode": mode,
    }
    if mode == "drg":
        base["medical_report"] = result.get("medical_report", {})
        base["treatment_plan"] = result.get("treatment_plan", {})
        base["drg_result"] = result.get("drg_result", {})
        base["emr_data"] = result.get("emr_data", {})
        save_info = _save_drg_result(request.query, result)
        base["save_info"] = save_info
    elif mode == "docgen":
        base["doc_final"] = result.get("doc_final", "")
        base["doc_type"] = result.get("doc_type", "")
        base["review_report"] = result.get("review_report", {})
    elif mode == "tcgen":
        base["tc_final"] = result.get("tc_final", "")
        base["tc_type"] = result.get("tc_type", "")
        base["review_report"] = result.get("review_report", {})
    elif mode == "vdoc":
        base["storage_path"] = result.get("storage_path", "")
        base["notification"] = result.get("notification", {})
    base["state"] = result
    return base


@app.get("/trace/replay")
def replay_trace():
    return {"events": event_bus.replay()}


# ── 通用 WebSocket 端点（支持 mode 切换） ──
@app.websocket("/ws/run")
async def websocket_run(websocket: WebSocket):
    await websocket.accept()
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    def listener(event: dict[str, Any]) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, event)

    unsubscribe = event_bus.subscribe(listener)
    try:
        payload = await websocket.receive_json()
        query = payload.get("query", "")
        language = normalize_language(payload.get("language"))
        mode = payload.get("mode", "drg")
        doc_type = payload.get("doc_type", "")
        tc_type = payload.get("tc_type", "")
        project_name = payload.get("project_name", "MedReasonerAgent")

        if not query and mode == "drg":
            await websocket.send_json({"event": "error", "message": "query is required"})
            return

        graph = select_graph(mode)
        state: dict[str, Any]
        if mode == "docgen":
            state = docgen_initial_state(query, language, doc_type, project_name)
        elif mode == "tcgen":
            state = tcgen_initial_state(query, language, tc_type, project_name)
        elif mode == "vdoc":
            state = vdoc_initial_state(query, language, doc_name=project_name, doc_type=doc_type, project_name=project_name)
        else:
            state = drg_initial_state(query, language)

        task = asyncio.create_task(asyncio.to_thread(graph.invoke, state))

        while True:
            if task.done() and queue.empty():
                result = task.result()
                # DRG 模式自动保存入组结果
                save_info = {}
                if mode == "drg":
                    save_info = _save_drg_result(query, result)
                    result["save_info"] = save_info
                await websocket.send_json(
                    {
                        "event": "complete",
                        "node": "complete",
                        "mode": mode,
                        "state": result,
                        "answer": result.get("answer", ""),
                        "trace": result.get("trace", []),
                        "save_info": save_info,
                    }
                )
                break

            try:
                event = await asyncio.wait_for(queue.get(), timeout=0.1)
                await websocket.send_json(event)
            except asyncio.TimeoutError:
                continue

    except WebSocketDisconnect:
        pass
    finally:
        unsubscribe()


# ── 文档生成专用端点 ──
@app.post("/docgen/generate")
def docgen_generate(request: RunRequest):
    """生成并保存文档：先 docgen 生成文档，再 vdoc 存储。"""
    # Step 1: 文档生成
    gen_state = docgen_initial_state(
        query=request.query,
        language=request.language,
        doc_type=request.doc_type,
        project_name=request.project_name,
    )
    gen_result = docgen_graph.invoke(gen_state)

    doc_final = gen_result.get("doc_final", "")
    if not doc_final:
        # 审核未通过，用格式化版本
        doc_final = gen_result.get("doc_formatted", gen_result.get("doc_draft", ""))

    # Step 2: 虚拟文档系统存储
    vdoc_state = vdoc_initial_state(
        query=f"Store document: {request.doc_type}",
        language=request.language,
        doc_name=request.project_name,
        doc_content=doc_final,
        doc_type=gen_result.get("doc_type", request.doc_type),
        project_name=request.project_name,
    )
    vdoc_result = vdoc_graph.invoke(vdoc_state)

    return {
        "answer": vdoc_result.get("answer", ""),
        "doc_final": doc_final,
        "doc_type": gen_result.get("doc_type", ""),
        "review_report": gen_result.get("review_report", {}),
        "storage_path": vdoc_result.get("storage_path", ""),
        "notification": vdoc_result.get("notification", {}),
        "trace": gen_result.get("trace", []),
        "vdoc_trace": vdoc_result.get("trace", []),
    }


# ── 测试用例生成专用端点 ──
@app.post("/tcgen/generate")
def tcgen_generate(request: RunRequest):
    """生成并保存测试用例：先 tcgen 生成用例，再 vdoc 存储。"""
    # Step 1: 测试用例生成
    gen_state = tcgen_initial_state(
        query=request.query,
        language=request.language,
        tc_type=request.tc_type,
        project_name=request.project_name,
    )
    gen_result = tcgen_graph.invoke(gen_state)

    tc_final = gen_result.get("tc_final", "")
    if not tc_final:
        tc_final = gen_result.get("tc_formatted", gen_result.get("tc_draft", ""))

    # Step 2: 虚拟文档系统存储
    # tc_type → doc_type 映射，用于 VDoc 存储命名
    tc_type_map = {
        "normal": "tc_normal",
        "boundary": "tc_boundary",
        "abnormal": "tc_abnormal",
    }
    doc_type_for_storage = tc_type_map.get(gen_result.get("tc_type", "normal"), "tc_normal")

    vdoc_state = vdoc_initial_state(
        query=f"Store test cases: {gen_result.get('tc_type', 'normal')}",
        language=request.language,
        doc_name=request.project_name,
        doc_content=tc_final,
        doc_type=doc_type_for_storage,
        project_name=request.project_name,
    )
    vdoc_result = vdoc_graph.invoke(vdoc_state)

    return {
        "answer": vdoc_result.get("answer", ""),
        "tc_final": tc_final,
        "tc_type": gen_result.get("tc_type", ""),
        "review_report": gen_result.get("review_report", {}),
        "storage_path": vdoc_result.get("storage_path", ""),
        "notification": vdoc_result.get("notification", {}),
        "trace": gen_result.get("trace", []),
        "vdoc_trace": vdoc_result.get("trace", []),
    }


# ── 已保存文档列表 ──
@app.get("/docgen/docs")
def list_documents():
    """列出 generated_docs 中已保存的文档。"""
    import json
    import os

    index_path = os.path.join(os.path.dirname(__file__), "generated_docs", "index.json")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
        documents = [_attach_document_badges(doc) for doc in index.get("documents", [])]
        return {"documents": documents, "last_updated": index.get("last_updated", "")}
    return {"documents": [], "last_updated": ""}


def _attach_document_badges(doc: dict[str, Any]) -> dict[str, Any]:
    """Attach lightweight acceptance badges for the VDoc console."""
    enriched = dict(doc)
    badges: dict[str, Any] = {
        "content_review": _build_content_review_badge(enriched),
        "pdf": _build_pdf_badge(enriched),
    }
    if str(enriched.get("type", "")).startswith("tc_"):
        badges["replay"] = _build_replay_badge(enriched)
    enriched["badges"] = badges
    return enriched


def _build_content_review_badge(doc: dict[str, Any]) -> dict[str, Any]:
    storage_path = str(doc.get("path", ""))
    doc_type = str(doc.get("type", ""))
    try:
        path = resolve_generated_path(storage_path)
        content = path.read_text(encoding="utf-8")
        if doc_type.startswith("tc_"):
            tc_type = doc_type.replace("tc_", "", 1) or "normal"
            result = tc_reviewer_agent({
                "tc_formatted": content,
                "tc_type": tc_type,
                "language": "zh",
                "trace": [],
            })
        else:
            result = doc_reviewer_agent({
                "doc_formatted": content,
                "doc_type": doc_type or "requirements",
                "language": "zh",
                "trace": [],
            })
        report = result.get("review_report", {})
        passed = bool(report.get("passed"))
        return {
            "status": "pass" if passed else "fail",
            "label": f"内容验收 {report.get('passed_count', 0)}/{report.get('total_count', 0)}",
            "detail": report.get("summary", ""),
        }
    except Exception as exc:
        return {
            "status": "fail",
            "label": "内容验收异常",
            "detail": str(exc),
        }


def _build_pdf_badge(doc: dict[str, Any]) -> dict[str, Any]:
    storage_path = str(doc.get("path", ""))
    try:
        path = resolve_generated_path(storage_path)
        rendered_dir = Path(__file__).resolve().parent / "generated_docs" / "rendered"
        exists = rendered_dir.exists() and any(rendered_dir.glob(f"{path.stem}_*.pdf"))
        return {
            "status": "pass" if exists else "pending",
            "label": "PDF 已生成" if exists else "PDF 未生成",
            "detail": "点击 PDF 预览可生成并打开" if not exists else "已存在可打开的 PDF 渲染文件",
        }
    except Exception as exc:
        return {
            "status": "fail",
            "label": "PDF 异常",
            "detail": str(exc),
        }


def _build_replay_badge(doc: dict[str, Any]) -> dict[str, Any]:
    storage_path = str(doc.get("path", ""))
    try:
        report = _build_replay_report(storage_path)
        passed = report.get("failed", 0) == 0 and report.get("total", 0) > 0
        return {
            "status": "pass" if passed else "fail",
            "label": f"回放 {report.get('passed', 0)}/{report.get('total', 0)}",
            "detail": f"真实入组回放通过率 {report.get('pass_rate', 0)}%",
        }
    except Exception as exc:
        return {
            "status": "fail",
            "label": "回放异常",
            "detail": str(exc),
        }


@app.get("/docgen/docs/{filename}")
def read_generated_document(filename: str):
    """Read one generated Markdown document for preview."""
    if filename != os.path.basename(filename) or not filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="invalid markdown filename")

    docs_dir = os.path.join(os.path.dirname(__file__), "generated_docs")
    path = os.path.abspath(os.path.join(docs_dir, filename))
    docs_root = os.path.abspath(docs_dir)
    if os.path.commonpath([docs_root, path]) != docs_root:
        raise HTTPException(status_code=400, detail="document path must stay inside generated_docs")
    if not os.path.exists(path) or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="document not found")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return {
        "filename": filename,
        "path": f"generated_docs/{filename}",
        "size": os.path.getsize(path),
        "content": content,
    }


@app.get("/docgen/export-package")
def export_delivery_package():
    """Export generated docs, PDFs, index, and replay reports as a delivery ZIP."""
    generated_dir = Path(__file__).resolve().parent / "generated_docs"
    index_path = generated_dir / "index.json"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="document index not found")

    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    exports_dir = generated_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = exports_dir / f"MedReasonerAgent_delivery_{timestamp}.zip"

    manifest: dict[str, Any] = {
        "project": "MedReasonerAgent",
        "created_at": datetime.now().isoformat(),
        "documents": [],
    }

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(index_path, "index.json")
        for doc in index.get("documents", []):
            storage_path = doc.get("path", "")
            try:
                doc_path = resolve_generated_path(storage_path)
            except (FileNotFoundError, ValueError):
                continue
            if doc_path.suffix.lower() != ".md":
                continue

            doc_type = doc.get("type", "document")
            doc_folder = f"documents/{doc_type}"
            zf.write(doc_path, f"{doc_folder}/{doc_path.name}")
            manifest["documents"].append({
                "name": doc.get("name", ""),
                "type": doc_type,
                "version": doc.get("version", ""),
                "path": storage_path,
                "included_markdown": f"{doc_folder}/{doc_path.name}",
            })

            try:
                rendered = render_markdown_pdf(storage_path=storage_path, output_name=doc_path.stem)
                pdf_path = resolve_generated_path(rendered["pdf_path"])
                zf.write(pdf_path, f"pdf/{pdf_path.name}")
            except Exception:
                pass

            if str(doc_type).startswith("tc_"):
                replay = _build_replay_report(storage_path)
                replay_name = doc_path.stem + "_replay_report.json"
                zf.writestr(
                    f"replay_reports/{replay_name}",
                    json.dumps(replay, ensure_ascii=False, indent=2),
                )

        zf.writestr("export_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=zip_path.name,
        content_disposition_type="attachment",
    )


@app.post("/docgen/render")
def docgen_render(request: RenderRequest):
    """Render a generated Markdown document to a PDF preview file."""
    try:
        result = render_markdown_pdf(
            markdown_text=request.content or None,
            storage_path=request.storage_path or None,
            output_name=request.output_name or "document",
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="document not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    result["pdf_url"] = result["pdf_url"]
    return result


@app.get("/docgen/rendered/{filename}")
def docgen_rendered(filename: str):
    """Serve rendered PDF previews from generated_docs/rendered."""
    try:
        path = rendered_pdf_path(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=filename,
        content_disposition_type="inline",
        headers={"Cache-Control": "no-store"},
    )


# ── 测试执行端点 ──
@app.get("/testing/run")
def testing_run():
    """
    运行 pytest，收集测试结果，立即返回（不调用 LLM）。
    """
    from tools.test_reporter import run_pytest

    test_data = run_pytest()
    return {
        "report_date": test_data["report_date"],
        "total": test_data["total"],
        "passed": test_data["passed"],
        "failed": test_data["failed"],
        "skipped": test_data["skipped"],
        "error": test_data["error"],
        "xfailed": test_data.get("xfailed", 0),
        "xpassed": test_data.get("xpassed", 0),
        "pass_rate": test_data["pass_rate"],
        "exit_code": test_data["exit_code"],
        "by_file": test_data["by_file"],
        "failed_tests": test_data["failed_tests"],
    }


@app.post("/testing/replay-doc")
def testing_replay_doc(request: ReplayDocRequest):
    """Extract JSON cases from a generated test document and replay DRG grouping."""
    return _build_replay_report(request.storage_path)


def _build_replay_report(storage_path: str) -> dict[str, Any]:
    try:
        doc_path = resolve_generated_path(storage_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="document not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    content = doc_path.read_text(encoding="utf-8")
    cases = extract_json_cases(content)
    results = []
    for case in cases:
        item: dict[str, Any] = {
            "index": case.index,
            "expected": case.expected,
            "passed": False,
            "error": case.error,
            "actual": {},
        }
        if case.emr is None:
            results.append(item)
            continue
        parsed = _parse_emr(json.dumps(case.emr, ensure_ascii=False))
        if not parsed:
            item["error"] = "EMR parse failed"
            results.append(item)
            continue
        actual = _do_drg_grouping(parsed)
        passed, reason = compare_drg_result(actual, case.expected)
        item.update({
            "input_emr": case.emr,
            "actual": {
                "mdc": actual.get("mdc", ""),
                "adrg": actual.get("adrg", ""),
                "drg": actual.get("drg", ""),
                "complication": actual.get("complication", ""),
                "confidence": actual.get("confidence", 0),
            },
            "passed": passed,
            "error": reason,
        })
        results.append(item)

    total = len(results)
    passed_count = sum(1 for item in results if item["passed"])
    return {
        "storage_path": storage_path,
        "total": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "pass_rate": round(passed_count / total * 100, 1) if total else 0.0,
        "cases": results,
    }


class ReportRequest(BaseModel):
    report_date: str = ""
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    error: int = 0
    xfailed: int = 0
    xpassed: int = 0
    pass_rate: float = 0.0
    exit_code: int = 0


# ── 测试报告生成端点 ──
@app.post("/testing/report")
def testing_report(request: ReportRequest | None = None, language: str = "zh"):
    """
    根据传入的测试数据调用大模型生成测试报告。
    若 request 为空则先运行 pytest。
    """
    from tools.test_reporter import build_test_report_prompt, run_pytest
    from tools.llm import call_llm

    if request is not None:
        test_data = request.model_dump()
    else:
        test_data = run_pytest()

    prompt = build_test_report_prompt(test_data, language=language)
    report_content = call_llm(prompt, metadata={"agent_system": "docgen", "doc_type": "testing"})

    return {"report": report_content}


# ── 测试文档统一生成（pytest 方案 + 执行数据 + LLM 报告） ──
@app.post("/testing/generate-doc")
def testing_generate_doc(language: str = "zh"):
    """
    统一流程：
    1. 运行 pytest 获取实时执行数据
    2. 调用大模型生成测试方案文档（复用 docgen pipeline）
    3. 调用大模型基于执行数据生成测试执行报告
    4. 合并为一个完整文档返回
    """
    from tools.test_reporter import (
        run_pytest,
        build_test_report_prompt,
        build_testing_doc_content,
    )
    from tools.llm import call_llm

    # Step 1: run pytest
    test_data = run_pytest()

    # Step 2: generate static test plan via docgen pipeline
    is_zh = language == "zh"
    plan_prompt = _build_testing_plan_prompt(language)
    test_plan = call_llm(plan_prompt, metadata={"agent_system": "docgen", "doc_type": "testing"})

    # Step 3: generate LLM execution report from pytest data
    report_prompt = build_test_report_prompt(test_data, language=language)
    llm_report = call_llm(report_prompt, metadata={"agent_system": "docgen", "doc_type": "testing"})

    # Step 4: merge
    doc_final = build_testing_doc_content(test_plan, test_data, llm_report)

    return {
        "doc_final": doc_final,
        "doc_type": "testing",
        "storage_path": "",
        "test_data": test_data,
    }


def _build_testing_plan_prompt(language: str) -> str:
    """Build a minimal prompt for the static test plan section."""
    from tools.test_reporter import REPORT_DATE

    is_zh = language == "zh"
    if is_zh:
        return f"""你是一名 QA 工程师。请为 MedReasonerAgent 项目生成一份完整的测试方案文档。

项目：MedReasonerAgent
生成日期：{REPORT_DATE}
语言：中文

文档必须严格包含以下章节（复制标题时保持完全一致，包括 "##" 前缀和编号）：

## 1. 测试策略
## 2. 单元测试方案
## 3. 集成测试方案
## 4. 系统测试方案
## 5. 验收测试方案
## 6. 测试环境
## 7. 缺陷管理

要求：
- 使用 Markdown 表格
- 包含属性表：| 属性 | 内容 | 列：项目名称(MedReasonerAgent)、文档类型(测试文档)、文档版本(V1.0)、生成日期({REPORT_DATE})、生成方式(AI 自动生成)、状态(草稿)
- 不得包含任何 TODO、TBD、待定等占位文本
- 文档末尾须包含：*本文档由 DocGen Agent 自动生成，状态为草稿，需人工审核确认。*
"""
    else:
        return f"""You are a QA engineer. Generate a complete test plan document for MedReasonerAgent.

Project: MedReasonerAgent
Generated date: {REPORT_DATE}
Language: English

Use these EXACT section headings:

## 1. 测试策略
## 2. 单元测试方案
## 3. 集成测试方案
## 4. 系统测试方案
## 5. 验收测试方案
## 6. 测试环境
## 7. 缺陷管理

Requirements:
- Use Markdown tables
- Include meta table: | 属性 | 内容 | with 项目名称(MedReasonerAgent), 文档类型(测试文档), 文档版本(V1.0), 生成日期({REPORT_DATE}), 生成方式(AI 自动生成), 状态(草稿)
- NO TODO, TBD or placeholder text
- End with: *本文档由 DocGen Agent 自动生成，状态为草稿，需人工审核确认。*
"""
