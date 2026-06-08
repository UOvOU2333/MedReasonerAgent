from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def call_llm(prompt: str, metadata: dict[str, Any] | None = None) -> str:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return offline_response(prompt, metadata=metadata)

    client = OpenAI(api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL") or None)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    request: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    if model != "deepseek-reasoner":
        request["temperature"] = float(os.getenv("LLM_TEMPERATURE", "0.2"))

    resp = client.chat.completions.create(**request)
    return resp.choices[0].message.content or ""


def offline_response(prompt: str, metadata: dict[str, Any] | None = None) -> str:
    text = " ".join(prompt.strip().split())

    # ── 文档生成 supervisor 分类（必须放在 docgen 完整文档生成之前）──
    # supervisor 只应返回分类字符串，不能走 _offline_docgen_dispatch 返回完整文档
    if "document generation supervisor" in text.lower() or "classify the user's request into one of three document types" in text.lower():
        import re
        # 从 prompt 中提取 Pre-set doc_type 作为最可靠的分类依据
        hint_match = re.search(r'Pre-set doc_type:\s*(\S+)', prompt)
        if hint_match:
            hint = hint_match.group(1).strip().lower()
            if hint in ("requirements", "architecture", "testing"):
                return hint
        return "requirements"

    # ── 优先：文档生成 fallback（必须放在最前面，避免被 DRG 关键词误匹配）──
    if metadata and metadata.get("agent_system") == "docgen":
        return _offline_docgen_dispatch(prompt, metadata)
    # 兜底：通过 prompt 特征识别文档生成
    if _is_docgen_prompt(text):
        return _offline_docgen_dispatch(prompt, metadata)

    # ── DRG 医疗推理 fallback ──
    if "Extract biomedical entities" in text:
        terms = [
            word.strip(".,:;()[]").lower()
            for word in text.split()
            if len(word.strip(".,:;()[]")) > 4
        ]
        return ", ".join(dict.fromkeys(terms[:6])) or "symptom, disease"
    if "Decide workflow" in text:
        return "deep-reasoning"
    if "structured medical understanding" in text:
        return (
            '{"possible_disease":"requires clinical confirmation",'
            '"symptoms":["extracted from query"],'
            '"risk_factors":["unknown"],'
            '"clinical_interpretation":"Preliminary AI-assisted case summary.",'
            '"severity_estimation":"undetermined"}'
        )
    if "Explain the biomedical reasoning" in text:
        return (
            "The system extracted query entities, retrieved the closest DRG graph context, "
            "ranked plausible medical reasoning paths, and generated a guarded treatment summary."
        )
    # DRG treatment — only match if NOT a docgen prompt
    if "treatment" in text.lower() and "DocGen" not in text:
        return (
            '{"options":["confirm diagnosis with licensed clinician",'
            '"symptom-directed management"],'
            '"drug_candidates":[],"confidence":"low",'
            '"warnings":["Educational output only; not medical advice."]}'
        )
    if "reasoning" in text.lower() and "DocGen" not in text:
        return "Query entities -> DRG concepts -> plausible mechanism -> clinical hypothesis."

    return "Preliminary medical reasoning generated from available query and graph context."


def _is_docgen_prompt(text: str) -> bool:
    """检测是否为文档生成类 prompt。"""
    docgen_markers = [
        "generating a requirements analysis document",
        "generating an architecture design document",
        "generating a test plan document",
        "docs/doc_spec.md",
        "DocGen Agent",
        "requirements analysis document",
        "architecture design document",
        "test plan document",
        "Document Generation Agent",
    ]
    return any(marker.lower() in text.lower() for marker in docgen_markers)


def _offline_docgen_dispatch(prompt: str, metadata: dict[str, Any] | None = None) -> str:
    """根据 prompt 内容分发到正确的文档生成 fallback。

    优先使用 metadata 中的 doc_type（最可靠，由前端/调用方显式指定）；
    回退到 prompt 关键词匹配（兼容无 metadata 的调用路径）。
    """
    # 优先：使用 metadata 中显式指定的 doc_type
    if metadata and metadata.get("doc_type"):
        doc_type = metadata["doc_type"]
        if doc_type == "architecture":
            return _offline_architecture_doc(prompt)
        if doc_type == "testing":
            return _offline_testing_doc(prompt)
        if doc_type == "requirements":
            return _offline_requirements_doc(prompt)

    # 回退：prompt 关键词匹配
    text = prompt.lower()
    if "requirements" in text or "需求分析" in text:
        return _offline_requirements_doc(prompt)
    if "architecture" in text or "架构" in text:
        return _offline_architecture_doc(prompt)
    if "testing" in text or "test plan" in text or "测试" in text:
        return _offline_testing_doc(prompt)
    # 默认返回需求分析文档
    return _offline_requirements_doc(prompt)


def _offline_requirements_doc(prompt: str) -> str:
    """生成离线需求分析文档模板。

    描述 MedReasonerAgent —— 基于 LangGraph 的多 Agent 生物医学知识图谱推理系统，
    核心能力为 DRG（疾病诊断相关分组）医保入组推理与临床决策支持演示。
    """
    import re
    from datetime import date
    project_match = re.search(r'Project:\s*(\S+)', prompt)
    project_name = project_match.group(1) if project_match else "MedReasonerAgent"
    today = date.today().isoformat()
    return f"""| 属性 | 内容 |
|------|------|
| **项目名称** | {project_name} |
| **文档类型** | 需求分析文档 |
| **文档版本** | V1.0 |
| **生成日期** | {today} |
| **生成方式** | AI 自动生成（DocGen Agent） |
| **状态** | 草稿 |

## 1. 引言

### 1.1 编写目的

本文档旨在对 {project_name} —— 多 Agent 医疗知识推理与可视化系统进行完整的需求分析。系统基于 LangGraph 编排多 Agent 工作流，结合 DRG 知识图谱检索和 LLM/SGLang 模型推理能力，实现可解释、可追踪、可视化的临床决策支持演示。

### 1.2 适用范围

本文档覆盖 {project_name} 的全部功能模块，包括：后端多 Agent 推理服务（FastAPI + LangGraph）、DRG 知识图谱检索、LLM/SGLang 模型推理与路由、WebSocket 事件流、前端 Agent 通信界面（Next.js + React Flow）和运行决策树可视化。

本文档不覆盖：真实医院 HIS/EMR 集成、医疗器械级诊断功能、药品处方合法性审核、用户账号体系与权限管理。

### 1.3 术语与缩写

| 术语/缩写 | 全称 | 说明 |
|-----------|------|------|
| DRG | Diagnosis Related Groups | 疾病诊断相关分组，用于医疗费用管理与临床路径分组 |
| KG | Knowledge Graph | 知识图谱，存储症状-疾病-DRG分组-治疗方案等关系 |
| LLM | Large Language Model | 大语言模型，用于医学实体抽取、推理、解释生成 |
| SGLang | SGLang | 高效 LLM 推理服务框架 |
| LangGraph | LangGraph | 基于有向图（DAG）的 LLM Agent 工作流编排框架 |
| React Flow | @xyflow/react | 前端节点图可视化库 |
| WebSocket | WebSocket | 双向实时通信协议，用于推送 Agent 执行事件 |
| Agent | Agent | 系统中承担单一推理步骤的独立处理单元 |
| DRGState | DRGState | 跨 Agent 传递的全局共享数据字典（TypedDict） |
| EventBus | EventBus | 发布/订阅模式的事件总线 |

## 2. 系统概述

### 2.1 项目背景

在医疗 AI 领域，多 Agent 系统正成为临床决策支持的重要技术方向。传统单模型推理存在过程不透明、推理链不可追溯等问题。{project_name} 旨在构建一个可解释、可追踪、可视化的多 Agent 医疗推理原型系统，聚焦于 **DRG（疾病诊断相关分组）医保入组推理**场景——根据患者症状和诊断信息，通过知识图谱检索和 LLM 推理，给出可能的 DRG 分组和治疗方案参考。

### 2.2 系统定位

本系统定位为**医疗推理原型与临床决策支持演示系统**：

- 是**医疗推理原型**，不是医疗诊断系统
- 是**临床决策支持演示**，不是临床决策执行系统
- 是**多 Agent 可解释推理教学系统**，不是医学教育考核系统
- 是**研究性原型**，不是生产级医疗器械软件

### 2.3 建设目标

1. **多 Agent 流水线**：从用户输入自然语言医疗问题开始，依次完成实体抽取、病例理解、DRG 检索、医学推理、路径排序、治疗方案草案生成和最终解释输出的完整链路。
2. **可解释推理**：每一步 Agent 的决策过程可被用户审查，Agent 间传递的上下文可追溯。
3. **实时可视化**：通过 WebSocket 事件流驱动前端运行决策树，实时展示执行进度。
4. **模型可替换**：支持 DeepSeek、OpenAI 兼容 API、SGLang 等多种模型服务，通过环境变量配置即可切换。
5. **医疗安全**：所有输出包含 AI 生成声明、临床确认建议和风险提示。
6. **离线可运行**：未配置 API Key 时，系统通过确定性 fallback 机制仍可完整演示全链路。

### 2.4 系统边界

**系统范围包含：**
- 后端多 Agent 推理服务（FastAPI + LangGraph）
- DRG 知识图谱检索（kg/ 模块）
- LLM / SGLang 模型推理与模型路由（runtime/router.py）
- WebSocket 事件流推送（runtime/event_bus.py）
- 前端 Agent 通信界面（Next.js + React Flow）
- 运行决策树可视化（AgentGraph 组件）
- 文档自动生成子系统（DocGen Agent + VDoc Agent）

**系统范围不包含：**
- 真实医院 HIS/EMR 系统集成
- 医疗器械级诊断功能
- 药品处方合法性审核
- 用户账号和权限管理系统
- 多租户隔离与数据持久化

## 3. 用户需求分析

### 3.1 目标用户角色

| 角色 | 描述 | 关注点 |
|------|------|--------|
| 普通用户 | 希望体验医疗 AI 推理过程的用户 | 输出是否易懂、推理过程是否可信 |
| 医保审核员 | 模拟 DRG 入组审核场景 | DRG 分组逻辑是否合理、路径是否可追溯 |
| 研发人员 | 医疗 AI 原型研发或系统集成工程师 | Agent 间数据传递、链路完整性、模型切换 |
| 教学人员 | 医疗 AI 课程或科研项目的演示人员 | 运行树是否清晰展示决策过程 |

### 3.2 用户场景分析

**场景一：医疗推理演示**：用户输入医疗问题（如"患者胸痛、发热，有糖尿病风险和炎症指标异常"），系统返回完整推理过程和结果，包含 Agent 分步执行说明、医疗报告摘要、治疗方案草案和风险提示。

**场景二：DRG 入组审核模拟**：医保审核员输入患者诊断信息，系统通过知识图谱检索症状→疾病→DRG 分组的映射关系，展示多跳推理路径和入组依据。

**场景三：多 Agent 通讯调试**：研发人员检查 Agent 间的数据传递，展开内部上下文查看原始输出和状态字段值，通过运行决策树查看执行路径。

**场景四：模型切换验证**：研发人员通过修改环境变量切换推理引擎（LLM/SGLang），验证不同模型服务下的执行行为和推理结果差异。

### 3.3 用户故事

| 编号 | 角色 | 需求描述 | 优先级 | 验收条件 |
|------|------|----------|--------|----------|
| US-01 | 普通用户 | 输入医疗问题后看到自然语言解释，而非内部变量 | 高 | 默认消息为自然语言 Markdown |
| US-02 | 普通用户 | 看到运行树展示系统每一步的决策过程 | 高 | 运行树随执行实时更新 |
| US-03 | 普通用户 | 医疗建议包含风险提示和免责声明 | 高 | 每条医疗输出含 warning |
| US-04 | 医保审核员 | 查看 DRG 分组的推理依据和关联路径 | 高 | 推理路径展示症状→疾病→DRG 完整链路 |
| US-05 | 研发人员 | 展开内部详情查看 Agent 间传递的数据 | 中 | 内部上下文默认折叠，可手动展开 |
| US-06 | 研发人员 | 模型服务通过配置切换，无需修改业务代码 | 中 | 修改 .env 即可切换模型服务 |
| US-07 | 研发人员 | 无 API Key 时全链路可运行 | 高 | offline fallback 返回确定性文本 |
| US-08 | 教学人员 | 运行树纵向排列，同层候选水平排列 | 中 | 运行树布局符合要求 |

### 3.4 用例分析

| 编号 | 名称 | 参与者 | 前置条件 | 基本流程 |
|------|------|--------|----------|----------|
| UC-01 | 执行医疗推理 | 普通用户 | 后端服务已启动 | 输入 query → 选择语言 → 发送 → 系统执行多 Agent 推理链路 → 前端实时展示 Agent 消息和运行树 → 显示最终答案 |
| UC-02 | DRG 入组推理 | 医保审核员 | 后端服务已启动 | 输入诊断信息 → Entity Agent 抽取实体 → Retrieval Agent 检索 DRG 子图 → Reasoning Agent 推演入组路径 → 输出 DRG 分组和治疗方案 |
| UC-03 | 查看内部上下文 | 研发人员 | 已完成至少一次推理 | 在对话区找到 Agent 消息 → 点击"查看 Agent 内部传递内容" → 展开原始输出和上下文摘要 |
| UC-04 | 切换推理引擎 | 研发人员 | 有对应 API Key | 修改 .env 中 REASONING_ENGINE → 重启服务 → 运行推理 → 运行树显示对应引擎选项 |

## 4. 功能需求

### 4.1 多 Agent 推理链路

系统采用 LangGraph 编排固定的线性多 Agent 流水线，各 Agent 通过共享 DRGState 字典传递信息：

```
supervisor → entity → medical_report → retrieval → reasoning → ranking → treatment_plan → explain
```

| 编号 | Agent | 功能 | 输入 | 输出 |
|------|-------|------|------|------|
| FR-01 | Supervisor | 意图分类，判断推理模式（simple/multi-hop/deep-reasoning） | query, language | plan.mode |
| FR-02 | Entity | 从用户 query 中抽取生物医学实体 | query, language | entities[] |
| FR-03 | Medical Report | 将 query 分析为结构化病例理解 | query, language | medical_report{{possible_disease, symptoms, risk_factors, severity}} |
| FR-04 | Retrieval | 基于抽取的实体检索 DRG 知识图谱子图 | entities[] | subgraph{{nodes, edges, hops}} |
| FR-05 | Reasoning | 基于实体和图谱上下文生成医学推理路径 | entities, subgraph | reasoning_paths[] |
| FR-06 | Ranking | 对候选推理路径进行排序 | reasoning_paths | ranked_paths[] |
| FR-07 | Treatment Plan | 生成治疗方案草案，包含风险提示 | medical_report, ranked_paths | treatment_plan{{options, drug_candidates, warnings}} |
| FR-08 | Explain | 汇总所有前置步骤，生成面向用户的最终自然语言解释 | ranked_paths, medical_report, treatment_plan | answer |

### 4.2 DRG 入组核心功能

系统围绕 DRG（疾病诊断相关分组）构建知识图谱和推理能力：

**FR-09：DRG 知识图谱** — 系统内置轻量级 DRG 知识图谱（`kg/drg_loader.py`），定义五类基本关系：

| 源节点类型 | 关系 | 目标节点类型 | 说明 |
|-----------|------|-------------|------|
| symptom | suggests | disease | 症状提示可能疾病 |
| disease | mapped_to | drg_group | 疾病映射到 DRG 分组 |
| disease | treated_by | treatment | 疾病对应治疗方式 |
| risk_factor | increases_risk_of | disease | 风险因素增加疾病概率 |
| test | confirms_or_rules_out | disease | 检查项目确定或排除疾病 |

**FR-10：DRG 子图检索** — `kg/query.py` 的 `get_subgraph(entities, hops)` 基于实体匹配图谱边，支持 1-3 跳扩展，返回子图 `{{nodes, edges, hops}}`。

**FR-11：DRG 入组推理流程** — 完整推理链路：Entity Agent 抽取医学实体 → Retrieval Agent 查找 symptom→disease→drg_group 映射 → Reasoning Agent 推演 DRG 入组路径 → Ranking Agent 排序候选路径 → Treatment Plan Agent 基于入组结果生成治疗方案。

### 4.3 可视化与交互

**FR-12：运行决策树** — 前端右侧使用 React Flow 渲染运行时决策树，每个 Agent 节点展示候选决策选项，实际选中路径以绿色标识。布局规则：纵向排列（每层 y+=184px）、水平候选（间距 96px）、延迟显示（未执行层级不提前渲染）。

**FR-13：对话式通信界面** — 前端左侧展示对话式 Agent 消息流，每条消息包含 Agent 名称、自然语言说明，内部上下文默认折叠，点击"查看 Agent 内部传递内容"可展开原始输出。

**FR-14：内部信息分层展示** — 用户可见层（始终显示）：Agent 名称、自然语言说明、执行摘要；内部详情层（默认折叠）：选中工具名、原始输出文本、上下文字段值。

### 4.4 模型服务与离线能力

**FR-15：模型服务配置化切换** — 通过环境变量支持 DeepSeek（`OPENAI_BASE_URL=https://api.deepseek.com`）、OpenAI 兼容 API、SGLang（`SGLANG_BASE_URL`）。`REASONING_ENGINE=llm|sglang` 环境变量控制推理引擎选择。

**FR-16：离线确定性 Fallback** — 未配置任何 API Key 时，所有 Agent 返回确定性 fallback 文本，保证全链路可运行和 UI 可测试。

**FR-17：Trace 回放** — `GET /trace/replay` 返回当前进程内 EventBus 已记录的全部事件，支持执行过程回溯审查。

## 5. 非功能需求

### 5.1 性能需求
- WebSocket 事件延迟：Agent 执行完成后 100ms 内到达前端
- 前端渲染帧率：运行树更新时不低于 30fps
- API 超时：同步 `/run` 接口超时上限 120s

### 5.2 可用性需求
- 支持中文和英文界面/输出语言切换
- 用户可见消息支持 Markdown 渲染（标题、列表、加粗、代码块）
- 首次使用显示空状态引导文案

### 5.3 可靠性需求
- 离线可运行：无 API Key 时全链路可跑通
- WebSocket 断连：前端显示错误状态，可重新连接
- 模型调用失败：不阻断整体链路，记录错误并继续

### 5.4 可维护性需求
- 严格分层：API / Graph / Runtime / Agent / KG / Tools / Frontend
- 模块化：每个 Agent 为独立函数，只承担单一推理步骤
- 配置外部化：所有模型配置通过 `.env` 管理

### 5.5 安全需求
- `.env`（含 API Key）不提交到 Git
- 所有医疗输出必须包含 warning 和免责声明
- 系统定位声明：不是医疗器械，不是诊断系统，不提供医疗建议
- API Key 不走前端，所有模型调用在后端执行

### 5.6 医疗安全与伦理约束
- 禁止声称给出最终诊断
- 禁止直接开具处方（drug_candidates 标明仅供参考）
- 所有输出提示"需经持证专业人员确认"
- 系统始终明确标识 AI 生成内容

## 6. 数据需求

### 6.1 DRGState 全局状态

| 字段名 | 类型 | 写入者 | 说明 |
|--------|------|--------|------|
| query | str | API 初始化 | 用户输入的自然语言医疗问题 |
| language | str | API 初始化 | 输出语言（zh/en） |
| entities | List[str] | Entity Agent | 抽取的医学实体列表 |
| subgraph | dict | Retrieval Agent | DRG 子图 |
| reasoning_paths | List | Reasoning Agent | 医学推理路径 |
| ranked_paths | List | Ranking Agent | 排序后推理路径 |
| medical_report | dict | Medical Report Agent | 结构化病例理解 |
| treatment_plan | dict | Treatment Plan Agent | 治疗方案草案 |
| answer | str | Explain Agent | 最终自然语言解释 |
| plan | dict | Supervisor Agent | 执行计划 |
| trace | List[dict] | 各 Agent | 执行轨迹日志 |

### 6.2 事件数据模型

EventBus 推送的事件对象：`event`（node_start/node_end/complete/error）、`node`（Agent 名称）、`decision_id`、`parent_decision_id`、`decision_options`（候选选项列表）、`selected_option`（实际选中）、`output`（Agent 输出）、`state`（当前状态快照）。

### 6.3 知识图谱数据模型

DRG 图谱边结构：`{{source: str, relation: str, target: str}}`。关系类型：suggests、mapped_to、treated_by、increases_risk_of、confirms_or_rules_out。子图结构：`{{nodes: List[str], edges: List[dict], hops: int}}`。

## 7. 外部接口需求

### 7.1 HTTP API 接口

| 方法 | 路径 | 请求体 | 响应 | 说明 |
|------|------|--------|------|------|
| GET | /health | - | {{"status": "ok"}} | 健康检查 |
| POST | /run | {{"query":"...", "language":"zh", "mode":"drg"}} | {{"answer":"...", "trace":[...], "medical_report":{{...}}, "treatment_plan":{{...}}}} | 同步执行智能体工作流 |
| GET | /trace/replay | - | {{"events": [...]}} | 回放 EventBus 历史事件 |
| POST | /docgen/generate | {{"query":"...", "doc_type":"requirements"}} | {{"doc_final":"...", "storage_path":"...", "review_report":{{...}}}} | 文档生成并存储 |

### 7.2 WebSocket 接口

| 路径 | 客户端发送 | 服务端事件流 |
|------|-----------|-------------|
| /ws/run | {{"query":"...", "language":"zh", "mode":"drg"}} | node_start → node_end → ... → complete |

WebSocket 连接建立后，后端每执行完一个 Agent 即推送 node_start/node_end 事件，前端实时更新对话消息和运行决策树。

### 7.3 环境变量契约

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| OPENAI_API_KEY | OpenAI 或兼容 API 密钥 | — |
| DEEPSEEK_API_KEY | DeepSeek API 密钥 | — |
| OPENAI_BASE_URL | API 服务地址 | — |
| OPENAI_MODEL | 默认模型名称 | gpt-4o-mini |
| REASONING_ENGINE | 推理引擎（llm/sglang） | sglang |
| SGLANG_BASE_URL | SGLang 推理服务地址 | — |
| NEXT_PUBLIC_API_BASE | 前端连接的后端地址 | http://localhost:8000 |

## 8. 约束与假设

### 8.1 技术约束
- LangGraph 工作流当前为固定线性拓扑（无条件分支）
- EventBus 为进程内实现（不支持分布式）
- DRG 图谱为内存加载（不支持大规模知识持久化）
- 无会话隔离（单用户原型阶段）

### 8.2 业务约束
- 系统不得用于真实临床诊断
- 系统为原型级别，不保证生产级可靠性
- 不保存真实患者隐私数据

### 8.3 假设条件
- 用户理解系统为原型，不会将输出作为医疗决策依据
- 使用外部模型时需要网络连接
- 当前阶段假设单用户操作模式

---

*本文档由 DocGen Agent 自动生成，状态为草稿，需人工审核确认。*
"""


def _offline_architecture_doc(prompt: str) -> str:
    """生成离线架构设计文档模板。"""
    import re
    project_match = re.search(r'Project:\s*(\S+)', prompt)
    project_name = project_match.group(1) if project_match else "MedReasonerAgent"
    return f"""| 属性 | 内容 |
|------|------|
| **项目名称** | {project_name} |
| **文档类型** | 架构设计文档 |
| **文档版本** | V1.0 |
| **生成日期** | 2026-06-08 |
| **生成方式** | AI 自动生成（DocGen Agent） |
| **状态** | 草稿 |

## 1. 总体架构
### 1.1 架构风格
{project_name} 采用分层架构（Layered Architecture），分后端服务层、运行时层、智能体层和前端展示层。

### 1.2 系统架构图
```
┌─────────────────────────────────────┐
│         用户浏览器 (Frontend)         │
│    Next.js + React Flow + Zustand   │
├─────────────────────────────────────┤
│       HTTP / WebSocket (JSON)       │
├─────────────────────────────────────┤
│         FastAPI 后端服务             │
│  ┌───────────────────────────────┐  │
│  │     Graph Layer (graph/)      │  │
│  ├───────────────────────────────┤  │
│  │    Runtime Layer (runtime/)   │  │
│  │  ┌────────┬────────┬───────┐  │  │
│  │  │Executor│EventBus│Router │  │  │
│  │  └────────┴────────┴───────┘  │  │
│  ├───────────────────────────────┤  │
│  │     Agent Layer (agents/)     │  │
│  │  (DRG / DocGen / VDoc agents) │  │
│  ├───────────────────────────────┤  │
│  │   KG Layer + Tools Layer      │  │
│  └───────────────────────────────┘  │
├─────────────────────────────────────┤
│        LLM API / SGLang            │
└─────────────────────────────────────┘
```

### 1.3 技术栈总览
| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Next.js, TypeScript, React Flow | 页面渲染与可视化 |
| 前端状态 | Zustand | 全局状态管理 |
| 后端框架 | FastAPI | REST/WebSocket 服务 |
| 工作流编排 | LangGraph | 多智能体流水线 |
| 模型调用 | OpenAI SDK | LLM API 调用 |
| 知识图谱 | 内存图谱 (kg/) | DRG 关系数据 |

## 2. 模块划分
### 2.1 模块总览
| 模块 | 路径 | 职责 | 依赖 |
|------|------|------|------|
| API 层 | app.py | HTTP 路由、WebSocket | graph, runtime |
| Graph 层 | graph/ | 状态定义、工作流编译 | agents, runtime |
| Runtime 层 | runtime/ | 执行器、事件总线、策略 | 无 |
| Agent 层 | agents/ | 各智能体实现 | tools, kg, runtime |
| KG 层 | kg/ | 知识图谱加载与查询 | 无 |
| Tools 层 | tools/ | LLM 客户端、trace 工具 | 无 |
| Frontend 层 | frontend/ | UI 组件、状态管理 | 后端 API |

### 2.2 各模块详细设计
#### Agent 层
- **DRG 入组智能体**：8 个子智能体线性流水线，处理医疗推理
- **文档生成智能体**：6 个子智能体，代码扫描→组稿→格式化→审核
- **虚拟文档系统智能体**：5 个子智能体，接收→验证→标记→存储→通知

## 3. 数据流设计
### 3.1 核心数据流
用户输入 → API 层（mode 路由）→ Graph 层（工作流选择）→ Agent 层（流水线执行）→ 事件总线 → 前端展示

### 3.2 状态管理
- 后端：TypedDict 状态在各 Agent 间传递
- 前端：Zustand Store 管理 UI 状态

### 3.3 事件机制
EventBus（发布/订阅模式）在 Agent 执行时发送 node_start/node_end 事件，前端通过 WebSocket 订阅。

## 4. 组件/服务通信
### 4.1 同步通信
| 方法 | 路径 | 请求 | 响应 | 说明 |
|------|------|------|------|------|
| POST | /run | query, language, mode | answer, trace, state | 执行智能体 |
| POST | /docgen/generate | query, doc_type | doc_final, storage_path | 生成并保存文档 |
| GET | /docgen/docs | - | documents[] | 文档列表 |
| GET | /health | - | status | 健康检查 |

### 4.2 异步通信
WebSocket /ws/run 支持实时事件流。

## 5. 技术选型
### 5.4 选型理由
| 技术项 | 选型 | 理由 | 替代方案 |
|--------|------|------|----------|
| 后端框架 | FastAPI | 异步支持、WebSocket 原生支持 | Flask, Django |
| 工作流 | LangGraph | 有向图编排、状态管理 | 自定义 DAG |
| 前端 | Next.js | SSR、React 生态 | Vite + React |
| 可视化 | React Flow | 节点图渲染 | D3.js, Cytoscape |
| 模型调用 | OpenAI SDK | 多模型兼容 | httpx 直接调用 |

## 6. 部署架构
### 6.1 部署拓扑
- 后端：单进程 FastAPI（uvicorn）
- 前端：Next.js dev server 或静态导出
- 依赖：外部 LLM API（DeepSeek / OpenAI / SGLang）

## 7. 安全设计
### 7.1 安全边界
- API Key 通过环境变量管理，不写入代码
- 生成的文档自动标记"草稿"状态和 AI 生成声明
- 前端不暴露后端 API Key

---

*本文档由 DocGen Agent 自动生成，状态为草稿，需人工审核确认。*
"""


def _offline_testing_doc(prompt: str) -> str:
    """生成离线测试文档模板。"""
    import re
    project_match = re.search(r'Project:\s*(\S+)', prompt)
    project_name = project_match.group(1) if project_match else "MedReasonerAgent"
    return f"""| 属性 | 内容 |
|------|------|
| **项目名称** | {project_name} |
| **文档类型** | 测试文档 |
| **文档版本** | V1.0 |
| **生成日期** | 2026-06-08 |
| **生成方式** | AI 自动生成（DocGen Agent） |
| **状态** | 草稿 |

## 1. 测试策略
### 1.1 测试层次
```
验收测试（E2E 场景验证）
    ^
集成测试（前后端联调、API 测试）
    ^
单元测试（模块级函数测试）
    ^
静态检查（构建、lint、安全审计）
```

### 1.2 测试方法
- 黑盒测试：API 接口功能测试
- 白盒测试：Agent 函数单元测试
- 手动测试：UI 交互验证
- 自动化测试：API 回归测试

## 2. 单元测试方案
### 2.1 测试范围
- Agent 层：每个 Agent 函数的输入/输出验证
- Graph 层：工作流编译正确性
- Runtime 层：EventBus 发布/订阅、Executor 生命周期
- Tools 层：LLM 调用封装、trace 工具

### 2.2 测试用例
| 编号 | 模块 | 测试项 | 输入 | 预期输出 |
|------|------|--------|------|----------|
| TC-01 | doc_supervisor | 文档类型分类 | query="生成需求分析" | doc_type="requirements" |
| TC-02 | doc_supervisor | 架构文档分类 | query="生成架构设计" | doc_type="architecture" |
| TC-03 | code_scanner | 代码扫描 | 项目根路径 | 返回模块清单 |
| TC-04 | context_collector | 上下文收集 | state with code_analysis | 返回上下文数据 |
| TC-05 | doc_composer | 文档组稿 | state with context | 返回 Markdown 字符串 |
| TC-06 | doc_formatter | 格式规范化 | 初稿文档 | 含元信息表的格式化文档 |
| TC-07 | doc_reviewer | 文档审核 | 格式化文档 | 审核报告含通过/失败 |
| TC-08 | doc_storer | 文件存储 | 文档内容 | 返回存储路径 |

### 2.3 覆盖率目标
- 代码行覆盖率 >= 80%
- Agent 函数覆盖率 100%

## 3. 集成测试方案
### 3.1 集成策略
自底向上：先测试单个 Agent，再测试 Agent 流水线，最后测试端到端 API。

### 3.2 接口测试用例
| 编号 | 接口 | 测试场景 | 请求 | 预期响应 |
|------|------|----------|------|----------|
| TC-I01 | POST /run (drg) | DRG 推理 | {{"query":"chest pain","mode":"drg"}} | 200, 含 answer 和 trace |
| TC-I02 | POST /run (docgen) | 文档生成 | {{"query":"需求分析","mode":"docgen","doc_type":"requirements"}} | 200, 含 doc_final |
| TC-I03 | POST /docgen/generate | 生成+存储 | {{"query":"架构设计","doc_type":"architecture"}} | 200, 含 storage_path |
| TC-I04 | GET /docgen/docs | 文档列表 | - | 200, 含 documents[] |

## 4. 系统测试方案
### 4.1 功能测试
- DRG 入组全链路测试
- 文档生成全链路测试
- 虚拟文档存储测试
- 前端三选项卡切换测试

### 4.2 性能测试
- 文档生成响应时间 < 120s
- WebSocket 事件延迟 < 100ms

### 4.3 安全测试
- 空 query 不可提交
- API Key 不泄露
- 生成文档包含 AI 声明

### 4.4 兼容性测试
- Chrome / Safari / Firefox 浏览器
- Python 3.10+
- Node.js 18+

## 5. 验收测试方案
### 5.1 验收标准
- [ ] DRG 选项卡可正常执行医疗推理
- [ ] 文档生成选项卡可生成三种文档
- [ ] 虚拟文档选项卡正常显示
- [ ] 生成的文档保存到 generated_docs/ 目录
- [ ] 文档格式符合 doc_spec.md 规范
- [ ] `npm run build` 前端构建成功
- [ ] 离线 fallback 模式下全链路可运行

### 5.2 验收流程
1. 环境准备：安装依赖，配置（或不配置）API Key
2. 功能验证：逐项测试三个智能体系统
3. 文档审核：检查生成文档的格式和质量
4. 签署验收

## 6. 测试环境
### 6.1 硬件环境
- CPU: >= 4 cores
- RAM: >= 8GB
- Disk: >= 2GB 可用空间

### 6.2 软件环境
- OS: macOS / Linux / Windows WSL
- Python: >= 3.10
- Node.js: >= 18
- 浏览器: Chrome 100+

### 6.3 测试数据
- 测试 query 使用脱敏医疗描述或文档生成指令

## 7. 缺陷管理
### 7.1 缺陷等级定义
| 等级 | 名称 | 说明 | 响应时间 |
|------|------|------|----------|
| P0 | 阻断 | 系统不可用，核心功能崩溃 | 2小时 |
| P1 | 严重 | 主要功能异常，影响使用 | 24小时 |
| P2 | 一般 | 次要功能异常，有替代方案 | 72小时 |
| P3 | 轻微 | UI 显示问题、建议性改进 | 下一迭代 |

### 7.2 缺陷跟踪流程
发现缺陷 → 记录（等级、复现步骤）→ 分配 → 修复 → 验证 → 关闭

---

*本文档由 DocGen Agent 自动生成，状态为草稿，需人工审核确认。*
"""
