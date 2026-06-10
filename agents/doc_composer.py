from datetime import date

from tools.llm import call_llm
from tools.trace import append_trace

TODAY = date.today().isoformat()


def doc_composer_agent(state):
    """
    根据文档类型、代码分析和上下文数据，组稿生成文档初稿。
    严格遵循 docs/doc_spec.md 定义的章节结构和内容要求。
    """
    language = state.get("language", "zh")
    doc_type = state.get("doc_type", "requirements")
    project_name = state.get("project_name", "MedReasonerAgent")
    code_analysis = state.get("code_analysis", {})
    context_data = state.get("context_data", {})

    modules_summary = _summarize_modules(code_analysis.get("modules", []))

    # 根据文档类型选择不同的 prompt 模板
    if doc_type == "requirements":
        prompt = _requirements_prompt(project_name, language, context_data, modules_summary, code_analysis)
    elif doc_type == "architecture":
        prompt = _architecture_prompt(project_name, language, context_data, modules_summary, code_analysis)
    else:
        prompt = _testing_prompt(project_name, language, context_data, modules_summary, code_analysis)

    draft = call_llm(prompt, metadata={"agent_system": "docgen", "doc_type": doc_type})
    state["doc_draft"] = draft
    append_trace(state, "doc_composer", f"Composed {doc_type} document draft ({len(draft)} chars)")
    return state


def _summarize_modules(modules: list) -> str:
    """将模块清单转换为可读摘要。"""
    lines = []
    for m in modules:
        lines.append(f"- [{m['layer']}] {m['name']}: {m['file']}")
    return "\n".join(lines[:50])


def _requirements_prompt(project_name: str, language: str, context: dict, modules: str, code: dict, generated_date: str = TODAY) -> str:
    is_zh = language == "zh"
    spec_ref = (
        "请严格参照 docs/doc_spec.md 中「需求分析文档格式」章节规定的结构生成。"
        if is_zh else
        "Follow the structure defined in docs/doc_spec.md section 'Requirements Analysis Document Format'."
    )

    return f"""
You are a technical writer generating a requirements analysis document.

Project: {project_name}
Generated date: {generated_date}
Description: {context.get('project_description', 'A software system')}

Available context:
- Architecture overview (CLAUDE.md): {context.get('architecture_overview', '')[:2000]}
- Requirements summary (docs/requirements.md): {context.get('requirements_summary', '')[:2000]}

Project modules:
{modules}

Code analysis summary:
- Python files: {code.get('total_py_files', 0)}
- TypeScript files: {code.get('total_ts_files', 0)}
- Key files: {code.get('key_files', {})}

{spec_ref}

Generate a complete requirements analysis document in {'Chinese' if is_zh else 'English'}.

CRITICAL — You MUST use these EXACT markdown section headings (copy them verbatim, including the "##" prefix and numbering).
Do NOT add extra top-level sections beyond these 8. Do NOT reorder or rename them:

## 1. 引言
## 2. 系统概述
## 3. 用户需求分析
## 4. 功能需求
## 5. 非功能需求
## 6. 数据需求
## 7. 外部接口需求
## 8. 约束与假设

Content per section:
- ## 1. 引言: 编写目的、适用范围、术语与缩写表格（术语|全称|说明）
- ## 2. 系统概述: 项目背景、系统定位、建设目标、系统边界
- ## 3. 用户需求分析: 至少3类目标用户角色表格、用户故事表格（编号|角色|需求描述|优先级|验收条件）、至少3个用例表格（编号|名称|参与者|前置条件|基本流程）
- ## 4. 功能需求: 至少8个 FR-XX 编号的功能需求，每个含编号|描述|输入|输出|处理逻辑
- ## 5. 非功能需求: 性能、可用性、可靠性、可维护性、安全
- ## 6. 数据需求: 全局状态数据模型表格、事件数据模型、知识图谱数据模型
- ## 7. 外部接口需求: HTTP API 表格（方法|路径|请求|响应|说明）、WebSocket 接口、环境变量表格
- ## 8. 约束与假设: 技术约束、业务约束、假设条件

Format requirements:
- Include the meta information table at the top: | 属性 | 内容 | with 项目名称, 文档类型, 文档版本, 生成日期 ({generated_date}), 生成方式, 状态
- Use Markdown tables where appropriate
- Each functional requirement must have a unique FR-XX number (FR-01, FR-02, ...)
- Use case tables must include: number, name, actor, preconditions, trigger, main flow
- User stories table must include: number, role, description, priority (高/中/低), acceptance criteria
- Document MUST end with: "*本文档由 DocGen Agent 自动生成，状态为草稿，需人工审核确认。*"
- ABSOLUTELY NO "TODO", "TBD", "待定", "待补充" or any placeholder text anywhere in the entire document
- If you reference the original requirements document, do NOT copy its meta-information table (which may contain "待定" placeholders). Create a fresh one.
- Do NOT include sections like "界面原型", "体系结构约束", "医疗安全与伦理约束", "测试与验收", "运行环境与部署" — these are NOT in the required 8 sections.

Document title: # {project_name} 需求分析文档
"""


def _architecture_prompt(project_name: str, language: str, context: dict, modules: str, code: dict, generated_date: str = TODAY) -> str:
    is_zh = language == "zh"
    spec_ref = (
        "请严格参照 docs/doc_spec.md 中「架构设计文档格式」章节规定的结构生成。"
        if is_zh else
        "Follow the structure defined in docs/doc_spec.md section 'Architecture Design Document Format'."
    )

    return f"""
You are a software architect generating an architecture design document.

Project: {project_name}
Generated date: {generated_date}
Description: {context.get('project_description', 'A software system')}

Architecture overview:
{context.get('architecture_overview', '')[:2500]}

Agent pipeline:
{context.get('agent_pipeline', '')}

Project modules:
{modules}

Code analysis:
- {code.get('total_py_files', 0)} Python files
- {code.get('total_ts_files', 0)} TypeScript files
- Key files: {code.get('key_files', {})}

{spec_ref}

Generate a complete architecture design document in {'Chinese' if is_zh else 'English'}.

CRITICAL — You MUST use these EXACT markdown section headings (copy them verbatim, including the "##" prefix and numbering):

## 1. 总体架构
## 2. 模块划分
## 3. 数据流设计
## 4. 组件/服务通信
## 5. 技术选型
## 6. 部署架构
## 7. 安全设计

Content per section:
- ## 1. 总体架构: 架构风格、ASCII 系统架构图（至少3层：展示层、业务逻辑层、数据层）、技术栈总览表格
- ## 2. 模块划分: 模块总览表格、每个模块详细设计（职责、接口、依赖）
- ## 3. 数据流设计: 核心数据流图、状态管理、事件机制
- ## 4. 组件/服务通信: REST API 表格（method|path|request|response|description）、WebSocket 事件、数据契约
- ## 5. 技术选型: 后端、前端、基础设施，含选型理由表格（technology|choice|reason|alternative）
- ## 6. 部署架构: 部署拓扑、环境配置
- ## 7. 安全设计: 安全边界、数据保护策略

Format requirements:
- Include the meta information table at the top: | 属性 | 内容 | with 项目名称, 文档类型, 文档版本, 生成日期 ({generated_date}), 生成方式, 状态
- Include ASCII architecture diagram showing at least 3 layers
- API table format: method | path | request | response | description
- Technology selection table: technology | choice | reason | alternative
- Document MUST end with: "*本文档由 DocGen Agent 自动生成，状态为草稿，需人工审核确认。*"
- NO "TODO", "TBD", "待定" or any placeholder text anywhere

Document title: # {project_name} 架构设计文档
"""


def _testing_prompt(project_name: str, language: str, context: dict, modules: str, code: dict, generated_date: str = TODAY) -> str:
    is_zh = language == "zh"
    spec_ref = (
        "请严格参照 docs/doc_spec.md 中「测试文档格式」章节规定的结构生成。"
        if is_zh else
        "Follow the structure defined in docs/doc_spec.md section 'Testing Document Format'."
    )

    return f"""
You are a QA engineer generating a test plan document.

Project: {project_name}
Generated date: {generated_date}
Description: {context.get('project_description', 'A software system')}

Architecture overview:
{context.get('architecture_overview', '')[:2000]}

Project modules:
{modules}

Code analysis:
- {code.get('total_py_files', 0)} Python files
- {code.get('total_ts_files', 0)} TypeScript files
- Key files: {code.get('key_files', {})}

{spec_ref}

Generate a complete test plan document in {'Chinese' if is_zh else 'English'}.

CRITICAL — You MUST use these EXACT markdown section headings (copy them verbatim, including the "##" prefix and numbering):

## 1. 测试策略
## 2. 单元测试方案
## 3. 集成测试方案
## 4. 系统测试方案
## 5. 验收测试方案
## 6. 测试环境
## 7. 缺陷管理

Content per section:
- ## 1. 测试策略: 测试层次（单元→集成→系统→验收）、测试方法
- ## 2. 单元测试方案: 至少6个 TC-XX 编号测试用例表格（编号|模块|测试项|输入|预期输出）、覆盖率目标
- ## 3. 集成测试方案: 集成策略、至少4个接口测试用例表格
- ## 4. 系统测试方案: 功能测试、性能测试、安全测试、兼容性测试
- ## 5. 验收测试方案: 验收标准 checklist（checkbox 格式）、验收流程
- ## 6. 测试环境: 硬件环境、软件环境、测试数据
- ## 7. 缺陷管理: P0/P1/P2/P3 四级缺陷等级定义、跟踪流程

Format requirements:
- Include the meta information table at the top: | 属性 | 内容 | with 项目名称, 文档类型, 文档版本, 生成日期 ({generated_date}), 生成方式, 状态
- Each test case must have a unique TC-XX number
- Acceptance criteria must use checkbox format: - [ ] item
- Coverage target must be quantified (e.g., ">= 80%")
- Defect severity levels: P0(critical/blocker), P1(high), P2(medium), P3(low)
- Document MUST end with: "*本文档由 DocGen Agent 自动生成，状态为草稿，需人工审核确认。*"
- NO "TODO", "TBD", "待定" or any placeholder text anywhere

Document title: # {project_name} 测试文档
"""
