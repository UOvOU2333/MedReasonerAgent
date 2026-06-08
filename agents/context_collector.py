import os
from tools.trace import append_trace

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def context_collector_agent(state):
    """
    收集项目背景信息：README、CLAUDE.md、需求文档、package.json 等。
    纯计算步骤，提取关键上下文供 doc_composer 使用。
    """
    context = {}

    # 读取 README.md
    readme_path = os.path.join(_PROJECT_ROOT, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            context["readme"] = f.read()[:3000]

    # 读取 CLAUDE.md（含架构说明）
    claude_path = os.path.join(_PROJECT_ROOT, "CLAUDE.md")
    if os.path.exists(claude_path):
        with open(claude_path, "r", encoding="utf-8") as f:
            context["architecture_overview"] = f.read()[:3000]

    # 读取需求文档
    req_path = os.path.join(_PROJECT_ROOT, "docs", "requirements.md")
    if os.path.exists(req_path):
        with open(req_path, "r", encoding="utf-8") as f:
            content = f.read()
            # 只提取关键章节（第1-4章）
            context["requirements_summary"] = content[:5000]

    # 读取前端 package.json
    pkg_path = os.path.join(_PROJECT_ROOT, "frontend", "package.json")
    if os.path.exists(pkg_path):
        import json
        try:
            with open(pkg_path, "r", encoding="utf-8") as f:
                pkg = json.load(f)
            context["frontend_deps"] = list(pkg.get("dependencies", {}).keys())
            context["frontend_dev_deps"] = list(pkg.get("devDependencies", {}).keys())
        except Exception:
            pass

    # 读取 CLAUDE.md 作为架构快速参考
    if "architecture_overview" in context:
        overview = context["architecture_overview"]
        # 提取 Agent pipeline 行
        for line in overview.split("\n"):
            if "supervisor" in line and "entity" in line:
                context["agent_pipeline"] = line.strip()
                break

    context["doc_spec_version"] = "V1.0"
    context["project_description"] = (
        "MedReasonerAgent is a multi-agent biomedical knowledge graph reasoning system. "
        "It uses LangGraph to orchestrate a linear pipeline of agents, FastAPI for the backend, "
        "and Next.js with React Flow for the frontend visualization."
    )

    state["context_data"] = context
    append_trace(state, "context_collector",
                 f"Collected context: README={'readme' in context}, CLAUDE={'architecture_overview' in context}, "
                 f"Requirements={'requirements_summary' in context}")
    return state
