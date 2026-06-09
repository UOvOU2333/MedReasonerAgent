from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph.workflow import build_graph, build_docgen_graph, build_tcgen_graph, build_vdoc_graph
from runtime.event_bus import event_bus

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
        return {"documents": index.get("documents", []), "last_updated": index.get("last_updated", "")}
    return {"documents": [], "last_updated": ""}
