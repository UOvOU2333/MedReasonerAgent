import os
from tools.trace import append_trace

# 项目根目录（绝对路径，在此硬编码以确保确定性）
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def code_scanner_agent(state):
    """
    扫描项目代码结构，提取文件树、模块清单和关键文件内容摘要。
    这是纯计算步骤，不依赖 LLM。
    """
    project_name = state.get("project_name", "MedReasonerAgent")

    files = []
    dirs = []
    for root, subdirs, filenames in os.walk(_PROJECT_ROOT):
        # 跳过不关注的目录
        subdirs[:] = [d for d in subdirs if d not in (
            "__pycache__", ".git", "node_modules", ".next",
            "frontend/.next", "frontend/node_modules",
        )]
        rel_root = os.path.relpath(root, _PROJECT_ROOT)
        if rel_root == ".":
            rel_root = ""
        for d in subdirs:
            dirs.append(os.path.join(rel_root, d).replace("\\", "/"))
        for f in filenames:
            if f.endswith((".pyc", ".pyo", ".DS_Store")):
                continue
            filepath = os.path.join(rel_root, f).replace("\\", "/")
            files.append(filepath)

    # 按类型分类
    py_files = [f for f in files if f.endswith(".py")]
    ts_files = [f for f in files if f.endswith((".ts", ".tsx"))]
    md_files = [f for f in files if f.endswith(".md")]
    other_files = [f for f in files if not f.endswith((".py", ".ts", ".tsx", ".md"))]

    # 提取模块清单（Python 和 TypeScript）
    modules = []
    for f in py_files:
        if f.startswith("agents/"):
            modules.append({"name": f.replace("agents/", "").replace(".py", ""), "layer": "agent", "file": f})
        elif f.startswith("graph/"):
            modules.append({"name": f.replace("graph/", "").replace(".py", ""), "layer": "graph", "file": f})
        elif f.startswith("runtime/"):
            modules.append({"name": f.replace("runtime/", "").replace(".py", ""), "layer": "runtime", "file": f})
        elif f.startswith("kg/"):
            modules.append({"name": f.replace("kg/", "").replace(".py", ""), "layer": "kg", "file": f})
        elif f.startswith("tools/"):
            modules.append({"name": f.replace("tools/", "").replace(".py", ""), "layer": "tool", "file": f})

    for f in ts_files:
        name = f.replace("frontend/", "").replace(".ts", "").replace(".tsx", "")
        modules.append({"name": name, "layer": "frontend", "file": f})

    code_analysis = {
        "project_root": _PROJECT_ROOT,
        "project_name": project_name,
        "total_py_files": len(py_files),
        "total_ts_files": len(ts_files),
        "total_md_files": len(md_files),
        "total_other_files": len(other_files),
        "modules": modules,
        "directories": sorted(dirs),
        "key_files": {
            "entry_point": "app.py" if "app.py" in files else None,
            "state_definition": "graph/state.py" if "graph/state.py" in files else None,
            "workflow": "graph/workflow.py" if "graph/workflow.py" in files else None,
            "frontend_page": "frontend/app/page.tsx" if "frontend/app/page.tsx" in files else None,
        },
    }

    state["code_analysis"] = code_analysis
    append_trace(state, "code_scanner",
                 f"Scanned {len(py_files)} Python files, {len(ts_files)} TypeScript files, {len(modules)} modules")
    return state
