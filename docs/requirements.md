# MedReasonerAgent 需求文档

## 1. 项目概述

MedReasonerAgent 是一个面向医疗知识推理场景的多 Agent 协作系统。系统使用 LangGraph 负责编排执行流程，结合 DRG 知识图谱检索、SGLang 或 OpenAI-compatible LLM API 推理、FastAPI 事件流服务，以及 Next.js + React Flow 前端，实现可解释、可追踪、可视化的医疗推理执行链。

系统定位为医疗推理与临床决策支持原型，不作为诊断、处方或医疗行为替代品。

## 2. 建设目标

系统需要实现以下目标：

- 支持用户输入自然语言医疗问题或病例描述。
- 通过多 Agent 流水线完成实体抽取、报告分析、DRG 检索、推理、排序、治疗方案生成和解释输出。
- 使用 LangGraph 管理 Agent 执行顺序和状态传递。
- 使用 Runtime 执行层统一包装节点执行，并向事件总线发出节点开始和结束事件。
- 支持 HTTP 一次性调用和 WebSocket streaming 调用。
- 前端使用 React Flow 实时展示 Agent 执行链、节点状态和 trace。
- 支持 DeepSeek、OpenAI、SGLang 等 OpenAI-compatible 模型服务切换。
- 在未配置模型密钥时支持 deterministic offline fallback，便于本地演示和调试。

## 3. 用户与使用场景

目标用户包括：

- 医疗 AI 原型研发人员。
- 医疗知识图谱和多 Agent 系统研究者。
- 希望观察医疗推理执行链的产品或算法团队。

典型场景：

- 输入患者症状、风险因素、检查结果等描述，系统生成结构化医疗理解。
- 系统检索 DRG 相关知识图谱上下文，辅助生成可能的医学推理路径。
- 系统输出治疗方案草案，并附带 warning 和限制说明。
- 前端实时观察每个 Agent 的执行状态和输出 trace。

## 4. 总体架构

执行链路：

```text
User Query
  -> FastAPI
  -> LangGraph Supervisor
  -> Runtime Executor
  -> Agent Layer
  -> Event Bus / Trace
  -> WebSocket
  -> React Flow UI
```

核心分层：

- API 层：`app.py`
- 图编排层：`graph/`
- Runtime 执行层：`runtime/`
- Agent 层：`agents/`
- 知识图谱层：`kg/`
- 模型和工具层：`tools/`
- 前端可视化层：`frontend/`

## 5. 目录结构要求

当前项目目录结构：

```text
MedReasonerAgent/
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── docs/
│   └── requirements.md
├── graph/
│   ├── state.py
│   └── workflow.py
├── runtime/
│   ├── __init__.py
│   ├── executor.py
│   ├── event_bus.py
│   └── router.py
├── agents/
│   ├── supervisor.py
│   ├── planner.py
│   ├── entity.py
│   ├── medical_report.py
│   ├── retrieval.py
│   ├── reasoning.py
│   ├── ranking.py
│   ├── treatment_plan.py
│   └── explain.py
├── kg/
│   ├── drg_loader.py
│   └── query.py
├── tools/
│   ├── llm.py
│   ├── sglang_client.py
│   └── trace.py
└── frontend/
    ├── app/
    ├── components/
    ├── lib/
    ├── store/
    ├── package.json
    └── tsconfig.json
```

## 6. 后端功能需求

### 6.1 FastAPI 服务

后端需要提供以下接口：

- `GET /health`
  - 返回服务健康状态。
- `POST /run`
  - 输入用户 query。
  - 同步执行 LangGraph。
  - 返回 answer、trace、medical_report、treatment_plan 和完整 state。
- `GET /trace/replay`
  - 返回当前进程内 EventBus 已记录事件。
- `WS /ws/run`
  - 输入用户 query。
  - streaming 返回节点执行事件。
  - 执行完成后返回 complete 事件。

### 6.2 LangGraph 工作流

工作流固定顺序：

```text
supervisor
-> entity
-> medical_report
-> retrieval
-> reasoning
-> ranking
-> treatment_plan
-> explain
```

每个节点必须接收并返回统一 state。

### 6.3 全局状态

`DRGState` 需要包含：

```python
query: str
entities: list[str]
subgraph: dict
reasoning_paths: list
ranked_paths: list
medical_report: dict
treatment_plan: dict
answer: str
plan: dict
trace: list[dict]
```

### 6.4 Runtime 执行层

Runtime 负责：

- 统一执行 LangGraph 节点。
- 在节点执行前发出 `node_start` 事件。
- 在节点执行后发出 `node_end` 事件。
- 生成可被前端消费的 state snapshot。
- 支持 trace replay。

事件格式：

```json
{
  "event": "node_start",
  "node": "reasoning",
  "timestamp": 1234567890,
  "state": {}
}
```

## 7. Agent 功能需求

### 7.1 Supervisor Agent

职责：

- 判断当前 query 适合的推理模式。
- 写入 `state["plan"]`。
- 追加 trace。

### 7.2 Entity Agent

职责：

- 从用户 query 中抽取医学实体。
- 写入 `state["entities"]`。
- 追加 trace。

### 7.3 Medical Report Agent

职责：

- 将用户 query 分析为结构化病例理解。
- 输出可能疾病、症状、风险因素、临床解释、严重程度估计。
- 写入 `state["medical_report"]`。

### 7.4 Retrieval Agent

职责：

- 基于实体检索 DRG 知识图谱子图。
- 写入 `state["subgraph"]`。

### 7.5 Reasoning Agent

职责：

- 使用 SGLang 或 LLM API 生成医学推理路径。
- 基于实体和子图生成因果或机制链。
- 写入 `state["reasoning_paths"]`。

### 7.6 Ranking Agent

职责：

- 对推理路径进行排序。
- 写入 `state["ranked_paths"]`。

### 7.7 Treatment Plan Agent

职责：

- 基于 medical report 和 ranked paths 生成治疗方案草案。
- 输出 options、drug candidates、mechanism、confidence、warnings。
- 写入 `state["treatment_plan"]`。

### 7.8 Explain Agent

职责：

- 汇总推理路径、报告和治疗方案。
- 生成最终自然语言解释。
- 写入 `state["answer"]`。

## 8. 知识图谱需求

当前 DRG 知识图谱为可替换的轻量示例实现。

需求：

- `kg/drg_loader.py` 负责加载 DRG 图数据。
- `kg/query.py` 负责基于 entities 查询子图。
- 子图返回结构需要包含 `nodes`、`edges`、`hops`。
- 后续应支持替换为真实 DRG 数据源、Neo4j、RDF、GraphRAG 或向量检索。

## 9. 模型接入需求

### 9.1 OpenAI-compatible LLM

`tools/llm.py` 使用 OpenAI SDK，支持通过环境变量配置：

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL=
LLM_TEMPERATURE=0.2
```

DeepSeek 示例：

```env
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-flash
REASONING_ENGINE=llm
```

### 9.2 SGLang

`tools/sglang_client.py` 支持 SGLang OpenAI-compatible endpoint：

```env
SGLANG_BASE_URL=
SGLANG_MODEL=default
REASONING_ENGINE=sglang
```

当未配置 `SGLANG_BASE_URL` 时，reasoning agent 回退到普通 LLM 调用。

### 9.3 Offline Fallback

当没有配置 API key 时，系统需要返回 deterministic fallback 文本，保证：

- 本地开发不依赖外部模型。
- 前后端执行链可以完整验证。
- trace 和 UI 能正常演示。

## 10. 前端功能需求

前端使用 Next.js、React、React Flow、Zustand 实现。

### 10.1 Agent Communication 主界面

组件：`frontend/components/ConversationPanel.tsx`

需求：

- 主页面优先展示对话式通信界面。
- 对话内容需要同时包含用户输入和多 Agent 输出。
- 默认可见内容必须面向用户，以自然语言说明 Agent 正在做什么、得到什么结论。
- Agent 间真实传递的结构化上下文、原始输出和内部数据应放入可展开区域，不默认占用主阅读流。
- 每个 Agent 输出需要体现：
  - 当前 Agent 名称。
  - 已选择工具。
  - 面向用户的执行说明。
  - 传递给后续 Agent 的关键上下文摘要，默认折叠。
- 用户可以在底部输入 query 并发起推理。
- 必须提供 Agent 输出语言选择，至少支持中文和英语。

### 10.2 Tool Decision Tree

组件：`frontend/components/AgentGraph.tsx`

需求：

- 作为右侧窄列展示，不占用主工作区。
- 展示运行时决策树，形态为 `决策 -> 多个候选项 -> 选中项继续连接下一层决策`。
- 整体需要纵向排列：上层决策在上，下层决策在下。
- 同一层级的候选工具或动作需要水平排列。
- 尚未执行到的层级不得提前显示。
- 前端不得预设完整运行层级或默认工具候选，必须以服务端实时事件中的 `decision_options` 为准。
- 当前决策激活时高亮该层候选项。
- 决策完成后高亮实际选中的候选项，并用该候选项连接下一层决策。
- 只有实际执行路径和实际选中方案使用绿色；未选中的候选项保持中性颜色。
- 支持分支和后续扩展为 guarded cycle / retry loop。
- 支持 idle、active、complete 状态。

### 10.3 Trace Panel

组件：`frontend/components/TracePanel.tsx`

需求：

- 展示每个 Agent 的执行状态。
- 展示最近事件日志。
- 状态包括 WAIT、RUNNING、OK。

### 10.4 Medical Report UI

组件：`frontend/components/ReportCard.tsx`

需求：

- 展示 medical report 输出。
- 展示 AI-generated warning。

### 10.5 Treatment Plan UI

组件：`frontend/components/TreatmentCard.tsx`

需求：

- 展示 treatment plan 输出。
- 展示医疗限制和 warning。

### 10.6 状态管理与通信

- `frontend/store/traceStore.ts` 管理 events、activeNode、completedNodes、finalState、answer。
- `frontend/store/traceStore.ts` 还需要管理 messages、availableTools、selectedTools。
- `frontend/lib/websocket.ts` 管理 WebSocket streaming。
- `frontend/lib/api.ts` 管理 HTTP API 调用。

## 11. 配置需求

`.env` 用于本地真实配置，不提交。

`.env.example` 用于提交模板。

关键变量：

```env
OPENAI_API_KEY=
DEEPSEEK_API_KEY=
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-flash
LLM_TEMPERATURE=0.2
REASONING_ENGINE=llm
SGLANG_BASE_URL=
SGLANG_MODEL=default
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

## 12. 运行方式

### 12.1 后端

```bash
cd /Users/zym/Documents/Code/Program/Agent/MedReasonerAgent
conda activate myenv
pip install -r requirements.txt
uvicorn app:app --reload
```

后端默认地址：

```text
http://127.0.0.1:8000
```

### 12.2 前端

```bash
cd /Users/zym/Documents/Code/Program/Agent/MedReasonerAgent/frontend
conda activate myenv
npm install
npm run dev
```

前端默认地址：

```text
http://localhost:3000
```

## 13. 非功能需求

- Python 版本不低于 3.10。
- 后端使用 FastAPI。
- 图编排使用 LangGraph。
- 前端使用 Next.js 和 React Flow。
- 支持 WebSocket streaming。
- 支持 trace replay。
- 支持模型服务切换。
- 不提交 `.env`、`node_modules/`、`.next/`、`__pycache__/` 等本地文件。
- 医疗相关输出必须包含免责声明或 warning。

## 14. 验收标准

后端验收：

- `GET /health` 返回 `{"status": "ok"}`。
- `POST /run` 返回 HTTP 200。
- trace 至少包含以下节点：
  - supervisor
  - entity
  - medical_report
  - retrieval
  - reasoning
  - ranking
  - treatment_plan
  - explain
- 返回结果包含 `medical_report` 和 `treatment_plan`。

前端验收：

- `npm run build` 成功。
- 页面可以输入 query 并启动执行。
- React Flow 节点状态随 WebSocket 事件更新。
- Trace Panel 可以显示执行状态。
- ReportCard 和 TreatmentCard 能展示最终 state 内容。

安全与配置验收：

- `.env` 不进入 Git。
- `.env.example` 保留配置模板。
- `npm audit` 返回 0 vulnerabilities。
- 后端在无 API key 时仍可通过 fallback 跑通全链路。

## 15. 后续扩展方向

- 接入真实 DRG 数据库或 Neo4j。
- 增加 Agent 条件分支和 guarded cycle。
- 增加真实路径 ranking score。
- 增加 trace 持久化和历史回放。
- 增加用户会话、任务 ID 和多用户隔离。
- 增加模型路由策略，支持 DeepSeek、Qwen、OpenAI、SGLang 多模型协作。
- 增加医疗安全规则和敏感输出过滤。
