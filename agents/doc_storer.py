import json
import os
import shutil
from datetime import datetime, timezone
from tools.trace import append_trace

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_GENERATED_DIR = os.path.join(_PROJECT_ROOT, "generated_docs")
_INDEX_FILE = os.path.join(_GENERATED_DIR, "index.json")


def doc_storer_agent(state):
    """
    将文档保存到文件系统（generated_docs/ 目录）。
    遵循虚拟文档系统存储规范：
    - 同名文件覆盖前备份
    - 更新 index.json
    """
    doc_content = state.get("doc_content", "")
    metadata = state.get("doc_metadata", {})
    doc_name = metadata.get("doc_name", state.get("doc_name", "untitled"))
    doc_type = metadata.get("doc_type", state.get("doc_type", "unknown"))
    version = metadata.get("version", "V1.0")
    project_name = state.get("project_name", "MedReasonerAgent")

    # 确保目录存在
    os.makedirs(_GENERATED_DIR, exist_ok=True)

    # 构建文件名
    filename = f"{project_name}_{doc_type}_{version}.md"
    filepath = os.path.join(_GENERATED_DIR, filename)

    # 同名文件备份
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{project_name}_{doc_type}_{version}_backup_{timestamp}.md"
        backup_path = os.path.join(_GENERATED_DIR, backup_name)
        shutil.copy2(filepath, backup_path)
        append_trace(state, "doc_storer", f"Backed up existing file to {backup_name}")

    # 写入文档文件
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(doc_content)

    # 更新索引
    index = _load_index()
    _update_index(index, doc_name, doc_type, version, filename)
    _save_index(index)

    try:
        storage_path = os.path.relpath(filepath, _PROJECT_ROOT)
    except ValueError:
        # Windows: filepath and _PROJECT_ROOT may be on different drives
        storage_path = filepath

    state["storage_path"] = storage_path
    append_trace(state, "doc_storer", f"Stored: {storage_path} ({len(doc_content)} chars)")
    return state


def _load_index() -> dict:
    if os.path.exists(_INDEX_FILE):
        try:
            with open(_INDEX_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"documents": [], "last_updated": ""}


def _update_index(index: dict, doc_name: str, doc_type: str, version: str, filename: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    # 查找是否已存在同名记录
    for doc in index["documents"]:
        if doc["name"] == doc_name and doc.get("type") == doc_type and doc["version"] == version:
            doc["updated_at"] = now
            doc["path"] = f"generated_docs/{filename}"
            doc["status"] = "updated"
            index["last_updated"] = now
            return
    # 新记录
    index["documents"].append({
        "name": doc_name,
        "type": doc_type,
        "version": version,
        "created_at": now,
        "updated_at": now,
        "path": f"generated_docs/{filename}",
        "status": "draft",
    })
    index["last_updated"] = now


def _save_index(index: dict) -> None:
    with open(_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
