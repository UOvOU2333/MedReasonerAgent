# MedReasonerAgent 需求分析文档

**需求分析规格说明书**

---

## 文档首页

| 属性 | 内容 |
|------|------|
| **项目名称** | MedReasonerAgent：多 Agent 医疗知识推理与可视化系统 |
| **文档名称** | 需求分析规格说明书（Requirements Analysis Specification） |
| **文档版本** | V1.0 |
| **编制日期** | 2026 年 05 月 21 日 |
| **文档状态** | 评审稿 |
| **项目代号** | MRA-REQ-001 |
| **编制人** | 项目组 |
| **评审人** | （待定） |
| **批准人** | （待定） |

---

**版本历史**

| 版本号 | 日期 | 修订人 | 修订说明 |
|--------|------|--------|----------|
| V0.1 | 2026-05-20 | 项目组 | 初稿，整合 coursework 文档 |
| V0.5 | 2026-05-21 | 项目组 | 补充 DRG 入组、多 Agent 通讯、界面原型详细设计 |
| V1.0 | 2026-05-21 | 项目组 | 完整需求分析稿，提交评审 |

---

**文档密级**：内部公开

**版权声明**：本文档为 MedReasonerAgent 项目组内部工作成果，仅供课程评审、原型开发与团队协作使用。

---

**目录**

1. [引言](#1-引言)
   - 1.1 编写目的
   - 1.2 适用范围
   - 1.3 术语与缩写
   - 1.4 参考文献
2. [系统概述](#2-系统概述)
   - 2.1 项目背景
   - 2.2 系统定位
   - 2.3 建设目标
   - 2.4 系统边界
3. [用户需求分析](#3-用户需求分析)
   - 3.1 目标用户角色
   - 3.2 用户场景分析
   - 3.3 用户故事
   - 3.4 用例分析
   - 3.5 用户交互流程
4. [功能需求](#4-功能需求)
   - 4.1 用户输入与配置
   - 4.2 多 Agent 推理链路
   - 4.3 DRG 入组功能细化
   - 4.4 多 Agent 通讯机制
   - 4.5 运行决策树可视化
   - 4.6 Agent 通信界面
   - 4.7 内部信息折叠与展示
   - 4.8 医疗报告生成
   - 4.9 治疗方案生成
   - 4.10 模型服务切换
   - 4.11 离线 Fallback
   - 4.12 Trace 回放
5. [界面原型](#5-界面原型)
   - 5.1 整体布局
   - 5.2 对话面板
   - 5.3 运行决策树面板
   - 5.4 Trace 面板
   - 5.5 报告卡片
   - 5.6 治疗卡片
   - 5.7 交互状态说明
6. [非功能需求](#6-非功能需求)
   - 6.1 性能需求
   - 6.2 可用性需求
   - 6.3 可靠性需求
   - 6.4 可维护性需求
   - 6.5 可扩展性需求
   - 6.6 安全需求
7. [数据需求](#7-数据需求)
   - 7.1 全局状态数据模型
   - 7.2 事件数据模型
   - 7.3 前端状态数据模型
   - 7.4 知识图谱数据模型
8. [外部接口需求](#8-外部接口需求)
   - 8.1 HTTP API 接口
   - 8.2 WebSocket 接口
   - 8.3 环境变量契约
   - 8.4 Markdown 展示契约
9. [体系结构约束](#9-体系结构约束)
   - 9.1 总体架构
   - 9.2 模块划分
   - 9.3 设计原则
   - 9.4 技术约束
10. [医疗安全与伦理约束](#10-医疗安全与伦理约束)
    - 10.1 系统定位声明
    - 10.2 禁止行为
    - 10.3 必须提示内容
    - 10.4 数据安全
    - 10.5 模型风险管理
    - 10.6 伦理边界
11. [测试与验收](#11-测试与验收)
    - 11.1 测试策略
    - 11.2 后端测试用例
    - 11.3 前端测试用例
    - 11.4 模型配置测试
    - 11.5 验收标准
12. [运行环境与部署](#12-运行环境与部署)
    - 12.1 推荐运行环境
    - 12.2 后端运行
    - 12.3 前端运行
    - 12.4 配置文件说明
13. [约束与假设](#13-约束与假设)
    - 13.1 技术约束
    - 13.2 业务约束
    - 13.3 假设条件
14. [附录](#14-附录)
    - 附录 A：模块目录结构
    - 附录 B：环境变量完整列表
    - 附录 C：Agent 节点职责速查表

---

## 1. 引言

### 1.1 编写目的

本文档旨在对 MedReasonerAgent —— 多 Agent 医疗知识推理与可视化系统进行完整、规范的需求分析。文档严格参照传统软件工程实践，将需求分为用户需求、功能需求、非功能需求、数据需求、外部接口需求、安全伦理约束和测试验收等独立章节。各章节遵循可验证、可追溯的编写原则。

本文档的预期读者包括：

- **课程评审人员**：评估需求分析完整性、软件工程方法应用程度。
- **项目开发者**：作为原型开发与阶段性验证的基线文档。
- **项目维护者**：作为后续迭代与扩展的参考基线。

### 1.2 适用范围

本文档覆盖 MedReasonerAgent 系统的全部功能模块、外部接口、数据模型、安全边界和验收标准。具体范围包括：

- 后端多 Agent 推理服务（FastAPI + LangGraph）
- DRG 知识图谱检索
- LLM / SGLang 模型推理与模型路由
- WebSocket 事件流
- 前端 Agent 通信界面（Next.js + React Flow）
- 运行决策树可视化
- 医疗安全与伦理约束

本文档不覆盖以下内容：

- 与真实医院 HIS / EMR 系统的集成
- 医疗器械级诊断功能
- 药品处方合法性审核
- 用户账号体系与权限管理模块
- 多租户数据隔离

### 1.3 术语与缩写

| 术语/缩写 | 全称 | 说明 |
|-----------|------|------|
| DRG | Diagnosis Related Groups | 疾病诊断相关分组，用于医疗费用管理与临床路径分组 |
| SRS | Software Requirements Specification | 软件需求规格说明书 |
| LangGraph | LangGraph | 基于有向图（DAG）的 LLM Agent 工作流编排框架 |
| SGLang | SGLang | 高效 LLM 推理服务框架 |
| React Flow | @xyflow/react | 前端节点图可视化库 |
| WebSocket | WebSocket | 双向实时通信协议 |
| KG | Knowledge Graph | 知识图谱 |
| Agent | Agent | 系统中承担单一推理步骤的独立处理单元 |
| State | DRGState | 跨 Agent 传递的全局共享数据字典 |
| EventBus | EventBus | 发布/订阅模式的事件总线，用于执行过程通知 |
| Supervisor | Supervisor Agent | 系统入口 Agent，负责判断推理模式 |
| Trace | Trace | Agent 执行过程的日志记录序列 |

### 1.4 参考文献

| 编号 | 文献 | 说明 |
|------|------|------|
| [1] | `docs/coursework/01-user-requirements.md` | 用户需求说明 |
| [2] | `docs/coursework/02-software-requirements-specification.md` | 软件需求规格说明书 |
| [3] | `docs/coursework/03-architecture-design.md` | 体系结构与概要设计 |
| [4] | `docs/coursework/04-interface-contracts.md` | 接口与数据契约 |
| [5] | `docs/coursework/05-safety-and-ethics.md` | 医疗安全与伦理约束 |
| [6] | `docs/coursework/06-test-and-acceptance.md` | 测试与验收计划 |
| [7] | `docs/requirements.md` | 原系统需求文档 |
| [8] | `docs/requirements-writing-logic.md` | 需求文档撰写逻辑说明 |
| [9] | IEEE 830-1998 | IEEE 软件需求规格说明书推荐实践 |

---

## 2. 系统概述

### 2.1 项目背景

在医疗 AI 领域，多 Agent 系统正成为临床决策支持的重要技术方向。传统单模型推理存在过程不透明、推理链不可追溯等问题。MedReasonerAgent 旨在构建一个可解释、可追踪、可视化的多 Agent 医疗推理原型系统。

系统基于 LangGraph 编排多 Agent 工作流，结合 DRG 知识图谱检索和 LLM / SGLang 模型推理能力，通过 FastAPI 提供事件流服务，前端基于 Next.js 和 React Flow 实现实时推理过程可视化。

### 2.2 系统定位

本系统定位为**医疗推理原型与临床决策支持演示系统**，具体说明如下：

- 是**医疗推理原型**，不是医疗诊断系统。
- 是**临床决策支持演示**，不是临床决策执行系统。
- 是**多 Agent 可解释推理教学系统**，不是医学教育考核系统。
- 是**研究性原型**，不是生产级医疗器械软件。

### 2.3 建设目标

系统需要实现以下核心目标：

1. **多 Agent 流水线**：从用户输入自然语言医疗问题开始，依次完成实体抽取、病例理解、DRG 检索、医学推理、路径排序、治疗方案草案生成和最终解释输出的完整链路。
2. **可解释推理**：每一步 Agent 的决策过程可被用户审查，Agent 间传递的上下文可追溯。
3. **实时可视化**：通过 WebSocket 事件流驱动前端运行决策树，实时展示执行进度。
4. **模型可替换**：支持 DeepSeek、OpenAI-compatible API、SGLang 等多种模型服务，通过环境变量配置即可切换。
5. **医疗安全**：所有输出包含相应的 AI 生成声明、临床确认建议和风险提示。
6. **离线可运行**：在未配置 API Key 时，系统通过确定性 fallback 机制仍可完整演示全链路。

### 2.4 系统边界

**系统范围包含：**

- 后端多 Agent 推理服务
- LangGraph 工作流编排
- DRG 知识图谱检索
- LLM / SGLang 模型推理
- WebSocket 事件流
- 前端 Agent 通信界面
- 前端运行决策树

**系统范围不包含：**

- 真实医院 HIS / EMR 集成
- 医疗器械级诊断功能
- 药品处方合法性审核
- 用户账号和权限管理系统
- 多租户隔离与数据持久化
- 真实患者隐私数据的收集与存储

---

## 3. 用户需求分析

### 3.1 目标用户角色

系统定义四类目标用户角色，每类用户有不同的使用目标和关注点：

#### 3.1.1 普通用户

| 属性 | 说明 |
|------|------|
| 角色描述 | 希望体验医疗 AI 推理过程的一般用户 |
| 技术背景 | 无需编程或医疗专业知识 |
| 使用目标 | 输入医疗问题后看到自然语言解释，理解系统推理过程 |
| 关注点 | 输出是否易懂、界面是否直观、推理过程是否可信 |
| 典型场景 | 输入症状描述，观察系统如何分析并给出参考建议 |

#### 3.1.2 研发人员

| 属性 | 说明 |
|------|------|
| 角色描述 | 医疗 AI 原型研发人员或系统集成工程师 |
| 技术背景 | 熟悉 Python、LLM、知识图谱等技术栈 |
| 使用目标 | 调试 Agent 间数据传递、验证链路完整性、切换模型服务 |
| 关注点 | 内部上下文是否可展开查看、trace 是否完整、模型是否可切换 |
| 典型场景 | 展开 Agent 内部传递数据，检查 reasoning 路径的完整性 |

#### 3.1.3 教学人员

| 属性 | 说明 |
|------|------|
| 角色描述 | 医疗 AI 课程或科研项目的教学和演示人员 |
| 技术背景 | 了解 AI 基础概念，但不一定深入工程细节 |
| 使用目标 | 展示系统每一步的决策过程，用于教学演示 |
| 关注点 | 运行树是否清晰展示决策过程、输出是否适合课堂讲解 |
| 典型场景 | 课堂演示中通过运行树向学生解释 Agent 如何协同工作 |

#### 3.1.4 安全审查者

| 属性 | 说明 |
|------|------|
| 角色描述 | 负责评估系统安全性和伦理合规性的人员 |
| 技术背景 | 信息安全、医疗法规、伦理审查 |
| 使用目标 | 确认系统输出符合医疗安全和伦理要求 |
| 关注点 | 是否所有医疗输出都包含 warning、系统是否会误导用户 |
| 典型场景 | 审查系统输出的免责声明是否完备 |

### 3.2 用户场景分析

#### 3.2.1 场景一：医疗推理演示

**场景描述**：用户输入一段医疗问题或病例描述，系统返回完整的推理过程和结果。

**输入示例**：
```
患者出现胸痛、发热，同时有糖尿病风险和炎症指标异常。
```

**系统处理流程**：
1. Supervisor 判断推理模式。
2. Entity Agent 抽取关键医学实体。
3. Medical Report Agent 生成结构化病例理解。
4. Retrieval Agent 检索 DRG 知识图谱。
5. Reasoning Agent 生成医学推理路径。
6. Ranking Agent 排序推理路径。
7. Treatment Plan Agent 生成治疗方案草案。
8. Explain Agent 生成最终解释。

**用户可见输出**：
- 面向用户的自然语言推理说明
- Agent 分步执行过程（默认自然语言描述）
- 医疗报告摘要
- 治疗方案草案和风险提示
- 运行决策树

#### 3.2.2 场景二：多 Agent 通讯调试

**场景描述**：研发人员需要检查 Agent 间的数据传递是否正确。

**操作流程**：
1. 研发人员输入测试 query。
2. 前端默认展示面向用户的自然语言消息。
3. 研发人员点击"查看 Agent 内部传递内容"展开内部上下文。
4. 可查看每个 Agent 的原始输出、状态字段值、决策选项和选中工具。
5. 通过运行决策树查看执行路径和分支选择。

#### 3.2.3 场景三：模型切换验证

**场景描述**：研发人员需要验证系统在不同模型服务下的行为。

**操作流程**：
1. 配置 `.env` 中相应变量。
2. 启动系统。
3. 使用同一 query 运行。
4. 通过 trace 和运行树对比不同模型服务的执行差异。
5. 测试 offline fallback 行为。

#### 3.2.4 场景四：教学演示

**场景描述**：教学人员使用运行决策树向学生展示多 Agent 决策过程。

**操作流程**：
1. 教学人员输入医疗 query。
2. 运行决策树逐步展开。
3. 每个决策节点展示候选方案。
4. 实际选中方案以绿色标识。
5. 教学人员可沿执行路径讲解每一步的决策逻辑。

### 3.3 用户故事

| 编号 | 角色 | 需求描述 | 优先级 | 验收条件 |
|------|------|----------|--------|----------|
| US-01 | 普通用户 | 我希望输入医疗问题后看到自然语言解释，而不是内部变量或模型原始输出 | 高 | 默认消息为自然语言 Markdown |
| US-02 | 普通用户 | 我希望看到运行树展示系统每一步的决策过程 | 高 | 运行树随执行实时更新 |
| US-03 | 普通用户 | 我可以选择系统输出中文或英语 | 中 | 语言切换后全部 Agent 输出语言随之改变 |
| US-04 | 普通用户 | 我希望所有医疗建议都包含风险提示 | 高 | 每条医疗输出含 warning |
| US-05 | 研发人员 | 我希望展开内部详情查看 Agent 间传递的数据 | 中 | 内部上下文默认折叠，可手动展开 |
| US-06 | 研发人员 | 我希望模型服务可以通过配置切换，无需修改业务代码 | 中 | 修改 `.env` 即可切换模型服务 |
| US-07 | 研发人员 | 在无 API Key 时系统仍能跑通完整链路 | 高 | offline fallback 返回确定性文本 |
| US-08 | 教学人员 | 我希望运行树整体纵向排列，同层候选水平排列 | 中 | 运行树布局符合要求 |
| US-09 | 教学人员 | 我希望只有实际执行路径显示为绿色 | 低 | 选中路径绿色，未选中中性色 |
| US-10 | 系统维护者 | 我希望环境变量不被提交到 Git | 高 | `.env` 在 `.gitignore` 中 |
| US-11 | 安全审查者 | 我希望系统明确提示医疗输出不是诊断或处方 | 高 | 最终回复含免责声明 |

### 3.4 用例分析

#### 用例 1：执行医疗推理

| 属性 | 内容 |
|------|------|
| 用例编号 | UC-01 |
| 用例名称 | 执行医疗推理 |
| 参与者 | 普通用户 |
| 前置条件 | 后端服务已启动，前端页面已加载 |
| 触发条件 | 用户在输入框中输入医疗问题并点击发送 |
| 基本流程 | 1. 用户输入 query；2. 选择语言；3. 点击发送；4. 系统执行多 Agent 推理链路；5. 前端实时展示 Agent 消息和运行树；6. 最终显示答案 |
| 异常流程 | 模型调用失败时，fallback 继续执行；WebSocket 断开时前端显示错误 |
| 后置条件 | trace 记录完整，运行树展示完整执行路径 |

#### 用例 2：展开 Agent 内部上下文

| 属性 | 内容 |
|------|------|
| 用例编号 | UC-02 |
| 用例名称 | 查看 Agent 内部传递内容 |
| 参与者 | 研发人员 |
| 前置条件 | 已执行至少一次推理 |
| 基本流程 | 1. 在对话区找到 Agent 消息；2. 点击"查看 Agent 内部传递内容"；3. 展开原始输出和上下文摘要 |

#### 用例 3：切换模型服务

| 属性 | 内容 |
|------|------|
| 用例编号 | UC-03 |
| 用例名称 | 切换模型推理引擎 |
| 参与者 | 系统维护者 |
| 前置条件 | 有对应模型服务的有效 API Key |
| 基本流程 | 1. 修改 `.env` 中 `REASONING_ENGINE` 和相关配置；2. 重启后端服务；3. 运行推理；4. 运行树中显示对应的 reasoning 选项 |

### 3.5 用户交互流程

```
用户打开页面
    |
    v
页面显示空状态：提示输入医疗推理问题
    |
    v
用户选择语言（中文 / English）
    |
    v
用户输入 query
    |
    v
点击发送按钮 -> 按钮禁用，状态栏显示"多 Agent 推理中"
    |
    v
WebSocket 连接建立 -> 发送 query
    |
    v
后端依次执行：supervisor -> entity -> medical_report
              -> retrieval -> reasoning -> ranking
              -> treatment_plan -> explain
    |
    v
每个 Agent 执行完：
  - 对话区新增自然语言消息
  - 运行树新增决策节点和选中选项
  - 当前执行节点高亮
    |
    v
全部执行完成：
  - 对话区显示最终答案（Markdown 渲染）
  - 运行树展示完整执行路径（绿色）
  - 状态栏恢复"就绪"
```

---

## 4. 功能需求

### 4.1 用户输入与配置

**FR-01：用户输入自然语言医疗问题**

| 属性 | 内容 |
|------|------|
| 功能编号 | FR-01 |
| 功能描述 | 系统应提供文本输入区域，允许用户输入自然语言描述的医疗问题或病例信息 |
| 输入 | 自然语言文本，长度不限，推荐 20-500 字 |
| 输出 | 无直接输出，输入内容将作为 LangGraph 工作流的起始状态 |
| 约束 | 空输入不可提交 |

**FR-02：Agent 输出语言选择**

| 属性 | 内容 |
|------|------|
| 功能编号 | FR-02 |
| 功能描述 | 系统应提供语言选择器，用户可选择所有 Agent 的输出语言 |
| 选项 | 中文（`zh`）和 English（`en`） |
| 默认值 | 中文（`zh`） |
| 实现机制 | `language` 字段写入 `DRGState`，各 Agent 根据该字段构造 prompt |

### 4.2 多 Agent 推理链路

系统采用 LangGraph 编排固定的线性多 Agent 流水线：

```
supervisor -> entity -> medical_report -> retrieval -> reasoning -> ranking -> treatment_plan -> explain
```

各 Agent 的功能需求详述如下。

---

**FR-03：Supervisor Agent（意图分类）**

| 属性 | 内容 |
|------|------|
| 功能编号 | FR-03 |
| Agent 名称 | supervisor |
| 职责 | 分析用户 query，判断适合的推理模式 |
| 输入 | `state["query"]`、`state["language"]` |
| 处理逻辑 | 调用 LLM 判断流程模式：simple / multi-hop / deep-reasoning |
| 输出 | 写入 `state["plan"]` = {"mode": 决策结果} |
| 决策选项 | simple（简单回答）、multi-hop（多步推理）、deep-reasoning（深度推理） |
| 选择策略 | 基于 LLM 返回的 mode 字段 |

**FR-04：Entity Agent（实体抽取）**

| 属性 | 内容 |
|------|------|
| 功能编号 | FR-04 |
| Agent 名称 | entity |
| 职责 | 从用户 query 中抽取生物医学实体 |
| 输入 | `state["query"]`、`state["language"]` |
| 处理逻辑 | 调用 LLM 提取医学实体，以逗号分隔；若实体数 > 5 则选择 terminology_normalizer |
| 输出 | 写入 `state["entities"]` = [实体列表] |
| 决策选项 | entity_extractor（提取关键词）、terminology_normalizer（术语规范化）、symptom_parser（症状解析） |

**FR-05：Medical Report Agent（病例理解）**

| 属性 | 内容 |
|------|------|
| 功能编号 | FR-05 |
| Agent 名称 | medical_report |
| 职责 | 将用户 query 分析为结构化病例理解 |
| 输入 | `state["query"]`、`state["language"]` |
| 处理逻辑 | 调用 LLM 提取：可能疾病、症状、风险因素、临床解释、严重程度估计 |
| 输出 | 写入 `state["medical_report"]` = {"text": ... , "warning": "AI-generated..."} |
| 决策选项 | case_summarizer（整理病例摘要）、risk_factor_analyzer（分析风险因素）、severity_estimator（估计严重程度） |

**FR-06：Retrieval Agent（DRG 检索）**

| 属性 | 内容 |
|------|------|
| 功能编号 | FR-06 |
| Agent 名称 | retrieval |
| 职责 | 基于抽取的实体检索 DRG 知识图谱子图 |
| 输入 | `state["entities"]` |
| 处理逻辑 | 调用 `kg/query.py` 的 `get_subgraph()`，匹配实体与图谱边，默认 2 跳扩展 |
| 输出 | 写入 `state["subgraph"]` = {"nodes": [...], "edges": [...], "hops": 2} |
| 决策选项 | direct_drg_lookup（直接查找 DRG 关系）、multi_hop_expansion（多跳扩展）、fallback_subgraph（使用备用子图） |

**FR-07：Reasoning Agent（医学推理）**

| 属性 | 内容 |
|------|------|
| 功能编号 | FR-07 |
| Agent 名称 | reasoning |
| 职责 | 基于实体和图谱上下文生成医学推理路径 |
| 输入 | `state["entities"]`、`state["subgraph"]`、`state["language"]` |
| 处理逻辑 | 根据 `REASONING_ENGINE` 环境变量选择调用 LLM 或 SGLang |
| 输出 | 写入 `state["reasoning_paths"]` = [推理路径列表] |
| 决策选项 | llm_reasoner / deepseek_reasoner / sglang_reasoner（取决于环境变量配置） |

**FR-08：Ranking Agent（路径排序）**

| 属性 | 内容 |
|------|------|
| 功能编号 | FR-08 |
| Agent 名称 | ranking |
| 职责 | 对候选推理路径进行排序 |
| 输入 | `state["reasoning_paths"]` |
| 处理逻辑 | 当前为规则式占位实现（排序），后续可替换为 scoring 机制 |
| 输出 | 写入 `state["ranked_paths"]` = [排序后路径列表] |
| 决策选项 | path_ranker（排序路径）、confidence_scorer（可信度评分）、evidence_filter（证据筛选） |

**FR-09：Treatment Plan Agent（治疗方案生成）**

| 属性 | 内容 |
|------|------|
| 功能编号 | FR-09 |
| Agent 名称 | treatment_plan |
| 职责 | 生成治疗方案草案，包含风险提示 |
| 输入 | `state["medical_report"]`、`state["ranked_paths"]`、`state["language"]` |
| 处理逻辑 | 调用 LLM 生成：治疗选项、候选用药、机制解释、置信度、警告/限制 |
| 输出 | 写入 `state["treatment_plan"]` = {"text": ... , "warning": "..."} |
| 决策选项 | treatment_generator、drug_candidate_lookup、warning_checker |

**FR-10：Explain Agent（解释生成）**

| 属性 | 内容 |
|------|------|
| 功能编号 | FR-10 |
| Agent 名称 | explain |
| 职责 | 汇总所有前置步骤，生成面向用户的最终自然语言解释 |
| 输入 | `state["ranked_paths"]`、`state["medical_report"]`、`state["treatment_plan"]`、`state["language"]` |
| 处理逻辑 | 调用 LLM 整合上下文，使用用户友好语言，包含医疗限制说明 |
| 输出 | 写入 `state["answer"]` = 最终解释文本 |
| 决策选项 | trace_summarizer、plain_language_explainer、limitation_writer |

### 4.3 DRG 入组功能细化

DRG（Diagnosis Related Groups，疾病诊断相关分组）入组是系统的核心功能模块之一。系统通过知识图谱对患者症状、疾病与 DRG 分组之间的映射关系进行检索和推理。

#### 4.3.1 DRG 知识图谱结构

系统内置轻量级 DRG 知识图谱示例，定义如下五类基本关系：

| 源节点类型 | 关系 | 目标节点类型 | 说明 |
|-----------|------|-------------|------|
| symptom | suggests | disease | 症状提示可能疾病 |
| disease | mapped_to | drg_group | 疾病映射到 DRG 分组 |
| disease | treated_by | treatment | 疾病对应治疗方式 |
| risk_factor | increases_risk_of | disease | 风险因素增加疾病概率 |
| test | confirms_or_rules_out | disease | 检查项目确定或排除疾病 |

**图谱加载模块**（`kg/drg_loader.py`）：

```
load_drg_graph() -> list[{source, relation, target}]
```

返回当前 DRG 图谱的全部三元组边列表。

#### 4.3.2 DRG 子图检索机制

**检索模块**（`kg/query.py`）：

```
get_subgraph(entities: list[str], hops: int = 2) -> dict
```

**检索算法**：

1. **实体规范化**：将输入 entities 列表中的每个实体做 `strip().lower()` 处理。
2. **边匹配**：遍历 DRG 图谱所有边，若边的 `source` 或 `target` 与任意规范化实体存在交集，则纳入子图。
3. **空实体兜底**：若 entities 为空或无法匹配到任何边，返回图谱的前 `hops + 1` 条边。
4. **节点集合**：收集所有匹配边的 source 和 target，去重后形成 nodes 列表。
5. **输出格式**：`{"nodes": [...], "edges": [...], "hops": hops}`

**检索策略决策**（由 `DecisionPolicy` 驱动）：

| 策略 | 触发条件 | 说明 |
|------|----------|------|
| direct_drg_lookup | 子图边数 ≤ 2 | 直接查找 DRG 关系，不扩展 |
| multi_hop_expansion | 子图边数 > 2 | 扩展多跳路径，探索间接关系 |
| fallback_subgraph | 实体匹配为空时 | 返回默认子图作为备用上下文 |

#### 4.3.3 DRG 入组推理流程

DRG 入组的完整推理流程贯穿多个 Agent：

```
1. Entity Agent 抽取医学实体
      |
2. Medical Report Agent 分析症状、风险因素、可能疾病
      |
3. Retrieval Agent 执行 DRG 子图检索
   - 基于实体查找 symptom -> disease 关系
   - 基于疾病查找 disease -> drg_group 关系
   - 多跳扩展相关 risk_factor 和 test 关系
      |
4. Reasoning Agent 基于子图推演 DRG 入组路径
   - 症状 -> 可能疾病 -> DRG 分组 -> 治疗方案
      |
5. Ranking Agent 排序候选入组路径
      |
6. Treatment Plan Agent 基于入组结果生成治疗方案
```

#### 4.3.4 DRG 数据扩展规划

当前实现为轻量示例数据，后续应支持以下扩展方向：

1. **接入真实 DRG 数据**：对接国家医保 DRG 分组方案数据。
2. **图数据库支持**：使用 Neo4j、ArangoDB 等图数据库替代内存图谱。
3. **图嵌入检索**：使用 GraphRAG 或图向量嵌入实现语义级图谱检索。
4. **动态图谱更新**：支持运行中动态添加或修改图谱边。
5. **多数据源融合**：融合 ICD 编码、SNOMED CT、UMLS 等医学标准术语体系。

### 4.4 多 Agent 通讯机制

多 Agent 通讯是本系统的核心设计。系统通过以下四个层面的机制实现 Agent 间的协作与信息传递：

#### 4.4.1 概述

多 Agent 通讯分为四个层次：

| 层次 | 模块 | 职责 |
|------|------|------|
| **状态传递层** | `graph/state.py` — `DRGState` | 定义跨 Agent 共享的数据结构，所有 Agent 通过读写同一 State 实现信息传递 |
| **编排层** | `graph/workflow.py` — LangGraph StateGraph | 定义 Agent 的执行顺序和有向边 |
| **执行控制层** | `runtime/executor.py` — `Executor` | 统一包装节点执行生命周期，注入事件发布 |
| **事件通知层** | `runtime/event_bus.py` — `EventBus` | 发布/订阅模式的事件总线，解耦执行过程与前端展示 |

#### 4.4.2 状态传递层：DRGState

`DRGState` 是系统中所有 Agent 共享的全局状态字典（TypedDict）。每个 Agent 接收当前 State，修改后返回更新后的 State。LangGraph 负责 State 的不可变传递。

```python
class DRGState(TypedDict):
    query: str              # 用户输入
    language: str           # 语言（zh / en）
    entities: List[str]     # 实体列表
    subgraph: dict          # DRG 子图
    reasoning_paths: List   # 推理路径
    ranked_paths: List      # 排序后路径
    medical_report: dict    # 病例报告
    treatment_plan: dict    # 治疗方案
    answer: str             # 最终答案
    plan: dict              # 执行计划
    trace: List[dict]       # 执行轨迹
```

**State 传递规范**：

- 每个 Agent 只能读取 State 中已有的字段，不得访问未定义字段。
- 每个 Agent 只能写入其职责范围内的字段，不得越权修改其他 Agent 的输出字段。
- State 中所有字段必须有合理的默认值（空字符串、空列表、空字典）。
- trace 通过 `tools/trace.py` 的 `append_trace()` 函数追加，每条记录为 `{"node": agent_name, "output": ...}`。

#### 4.4.3 编排层：LangGraph 工作流

LangGraph 的 `StateGraph` 定义了 Agent 的拓扑结构：

```
graph.set_entry_point("supervisor")

supervisor -> entity
entity -> medical_report
medical_report -> retrieval
retrieval -> reasoning
reasoning -> ranking
ranking -> treatment_plan
treatment_plan -> explain

graph.set_finish_point("explain")
```

**编排约束**：

- 当前为固定线性拓扑，无分支路由。
- 所有边为无条件的 `add_edge`，不涉及条件路由 `add_conditional_edges`。
- 后续可扩展为：supervisor 根据 plan mode 选择不同下游 Agent 路径。

#### 4.4.4 执行控制层：Executor

`Executor` 是 LangGraph 节点和执行逻辑之间的中间层，负责统一包装每个 Agent 节点的执行生命周期。

**执行生命周期**：

```
1. Executor.run_node(node_name, node_fn, state)
      |
2. DecisionPolicy.start_decision() -> 生成 Decision(decision_id, parent, options)
      |
3. EventBus.emit(node_start 事件) -> 前端收到 node_start
      |
4. node_fn(state) -> 实际 Agent 逻辑执行
      |
5. DecisionPolicy.end_decision() -> 生成 Decision(decision_id, parent, options, selected_option)
      |
6. EventBus.emit(node_end 事件) -> 前端收到 node_end
      |
7. 返回更新后的 state
```

**事件格式**：

`node_start` 事件：
```json
{
  "event": "node_start",
  "node": "reasoning",
  "decision_id": "reasoning",
  "parent_decision_id": "retrieval",
  "available_tools": ["llm_reasoner", "deepseek_reasoner"],
  "decision_options": ["llm_reasoner", "deepseek_reasoner"],
  "state": { /* state snapshot */ }
}
```

`node_end` 事件：
```json
{
  "event": "node_end",
  "node": "reasoning",
  "decision_id": "reasoning",
  "parent_decision_id": "retrieval",
  "decision_options": ["llm_reasoner", "deepseek_reasoner"],
  "selected_option": "deepseek_reasoner",
  "selected_tool": "deepseek_reasoner",
  "output": "Query entities -> DRG concepts -> plausible mechanism -> clinical hypothesis.",
  "state": { /* state snapshot */ }
}
```

#### 4.4.5 事件通知层：EventBus

`EventBus` 采用发布/订阅模式，解耦后端执行过程和前端 UI 更新。

**核心机制**：

- **订阅**：`event_bus.subscribe(listener)` — 注册回调函数，返回 unsubscribe 函数。
- **发布**：`event_bus.emit(event)` — 向所有注册的 listener 广播事件，自动附加 `timestamp`。
- **回放**：`event_bus.replay()` — 返回当前进程中已记录的所有事件，用于 `/trace/replay` API。

**线程安全**：使用 `threading.Lock` 保护 listeners 列表操作。

**事件消费**：

在 WebSocket 模式下，`app.py` 将 listener 注入 EventBus，事件通过 `asyncio.Queue` 传递到 WebSocket 发送协程：

```
EventBus.emit() -> listener() -> Queue.put_nowait() -> websocket.send_json()
```

#### 4.4.6 决策策略：DecisionPolicy

`DecisionPolicy` 负责为每个 Agent 节点生成候选决策选项和最终选中选项。

**父节点映射**（`GRAPH_PARENTS`）：

| 节点 | 父节点 |
|------|--------|
| supervisor | null（根节点） |
| entity | supervisor |
| medical_report | entity |
| retrieval | medical_report |
| reasoning | retrieval |
| ranking | reasoning |
| treatment_plan | ranking |
| explain | treatment_plan |

**决策选项生成规则**（每个节点最多 3 个候选选项）：

| 节点 | 候选选项 | 选择策略 |
|------|---------|----------|
| supervisor | simple, multi-hop, deep-reasoning | 根据 LLM 返回的 mode 字段 |
| entity | entity_extractor, terminology_normalizer, symptom_parser | entities > 5 则选 terminology_normalizer |
| medical_report | case_summarizer, risk_factor_analyzer, severity_estimator | 若 report 含 "severity" 则选 severity_estimator |
| retrieval | direct_drg_lookup, multi_hop_expansion, fallback_subgraph | edges > 2 则选 multi_hop_expansion |
| reasoning | llm_reasoner, deepseek_reasoner, sglang_reasoner | 根据环境变量 REASONING_ENGINE 和 OPENAI_MODEL |
| ranking | path_ranker, confidence_scorer, evidence_filter | ranked_paths > 1 则选 confidence_scorer |
| treatment_plan | treatment_generator, drug_candidate_lookup, warning_checker | 若 plan 含 "warning" 则选 warning_checker |
| explain | trace_summarizer, plain_language_explainer, limitation_writer | 默认选 plain_language_explainer |

#### 4.4.7 模型路由：ModelRouter

`ModelRouter` 封装模型调用策略，支持运行时切换推理引擎：

```
ModelRouter.reason(prompt, engine) -> str
ModelRouter.generate(prompt, metadata) -> str
```

**路由逻辑**：

| 配置 | 行为 |
|------|------|
| REASONING_ENGINE=sglang 且 SGLANG_BASE_URL 已配置 | 调用 SGLang `/v1/chat/completions` |
| REASONING_ENGINE=llm 或 SGLang 未配置 | 调用 OpenAI SDK（支持 DeepSeek 等兼容 API） |
| 未配置任何 API Key | 返回 deterministic offline fallback 文本 |

#### 4.4.8 Agent 间上下文传递示意图

```
User Query: "患者胸痛、发热，有糖尿病风险和炎症指标异常"
    |
[supervisor] plan.mode = "deep-reasoning"
    |  -> 传递：query, language, plan
[entity] entities = ["胸痛", "发热", "糖尿病", "炎症"]
    |  -> 传递：query, language, plan, entities
[medical_report] medical_report = {text, warning}
    |  -> 传递：query, language, plan, entities, medical_report
[retrieval] subgraph = {nodes, edges, hops}
    |  -> 传递：query, language, plan, entities, medical_report, subgraph
[reasoning] reasoning_paths = ["胸痛->冠心病->DRG F..."]
    |  -> 传递：query, language, ..., subgraph, reasoning_paths
[ranking] ranked_paths = [排序后路径]
    |  -> 传递：query, language, ..., reasoning_paths, ranked_paths
[treatment_plan] treatment_plan = {text, warning}
    |  -> 传递：query, language, ..., ranked_paths, treatment_plan
[explain] answer = "根据您的描述，系统分析了..."
    |
最终输出：answer + trace + 完整 state
```

### 4.5 运行决策树可视化

**FR-11：运行决策树**

| 属性 | 内容 |
|------|------|
| 功能编号 | FR-11 |
| 功能描述 | 前端右侧窄列实时展示运行时决策树，使用 React Flow 渲染 |
| 数据来源 | WebSocket 事件中的 `decision_id`、`parent_decision_id`、`decision_options`、`selected_option` |

**布局规则**：

| 规则 | 说明 |
|------|------|
| 纵向排列 | 上层决策在上，下层决策在下（每个层级 y += 184px） |
| 水平排列 | 同一层级的候选工具/动作水平分布（间距 96px） |
| 延迟显示 | 未执行的层级不提前渲染，仅展示已收到事件的层级 |
| 选中高亮 | 决策完成后高亮实际选中的候选项（绿色边框） |
| 执行路径 | 只有实际执行路径和选中方案使用绿色 |
| 未选中 | 未选中的候选选项保持中性色 |
| 当前激活 | 正在执行的节点高亮，候选区活跃状态 |

**节点类型**：

| 类型 | 说明 | 尺寸 |
|------|------|------|
| DecisionNode（决策节点） | 花括号菱形表达，展示 Agent 名称（中文/英文） | 128px × 42px+ |
| OptionNode（候选节点） | 圆角矩形，展示工具/动作名称 | 92px × 40px+ |

**状态样式**：

| 状态 | 决策节点样式 | 候选节点样式 |
|------|------------|------------|
| idle | 默认边框 + 灰色 | 浅灰背景 + 灰色文字 |
| active | 橙色边框 + 橙色文字 + 旋转图标 | 暖色背景 + 橙色边框 |
| complete | 绿色边框 + 绿色文字 + 对勾图标 | — |
| selected | — | 绿色边框 + 浅绿背景 + 绿色文字 |

**边样式**：

| 类型 | 样式 |
|------|------|
| 父决策 -> 候选 | 默认边 |
| 父决策 -> 候选（active） | 动画虚线 |
| 候选 -> 子决策 | 绿色实线，只渲染选中候选项的连线 |

### 4.6 Agent 通信界面

**FR-12：对话式通信界面**

| 属性 | 内容 |
|------|------|
| 功能编号 | FR-12 |
| 功能描述 | 前端左侧主区域展示对话式 Agent 通信界面 |
| 组件 | `ConversationPanel.tsx` |

**消息类型**：

| 角色 | 展示位置 | 图标 | 背景色 |
|------|---------|------|--------|
| user | 右对齐 | UserRound 图标（蓝绿色圆形） | 浅绿色 |
| agent | 左对齐 | Bot 图标（灰色圆形） | 白色 |
| system | 左对齐 | Bot 图标 | 白色 |

**消息内容**：

每条 Agent 消息包含：
- **标题**：Agent 名称（如 "Entity Agent"）
- **正文**：面向用户的自然语言执行说明（Markdown 渲染）
- **详情区**：可展开区域，默认折叠，包含：
  - 选中的工具/动作
  - Agent 原始输出
  - Agent 间传递的上下文摘要

**空状态**：无消息时显示引导文案和 Bot 图标。

**输入区**：底部固定，包含：
- 语言选择器（下拉框）
- 文本输入框（textarea，最大高度 180px）
- 发送按钮（Send 图标，运行中不可用）

### 4.7 内部信息折叠与展示

**FR-13：内部信息分层展示**

| 属性 | 内容 |
|------|------|
| 功能编号 | FR-13 |
| 功能描述 | 将 Agent 间真实传递的结构化上下文、原始输出和内部数据从默认展示流中分离，放入可展开区域 |

**分层原则**：

| 层级 | 默认状态 | 包含内容 |
|------|---------|----------|
| 用户可见层 | 始终显示 | Agent 名称、面向用户的自然语言说明、执行摘要 |
| 内部详情层 | 默认折叠 | 选中工具名、原始输出文本、上下文字段值（entities, subgraph, reasoning_paths 等截断展示） |

**实现要求**：

- 使用 HTML `<details><summary>` 元素实现折叠。
- 折叠标签文案：中文"查看 Agent 内部传递内容"，英文"View internal agent handoff"。
- 内部内容以 `<pre>` 标签展示，保留格式但不设固定宽度。

### 4.8 医疗报告生成

**FR-14：结构化病例理解**

| 属性 | 内容 |
|------|------|
| 功能编号 | FR-14 |
| 功能描述 | 系统应基于用户输入生成结构化病例理解，包含可能疾病、症状、风险因素、临床解释、严重程度估计 |
| 输出格式 | JSON 结构，由 Medical Report Agent 生成 |

**输出必须包含字段**：

| 字段 | 说明 |
|------|------|
| possible_disease | 可能疾病列表 |
| symptoms | 已识别的症状 |
| risk_factors | 风险因素 |
| clinical_interpretation | 临床解释 |
| severity_estimation | 严重程度估计 |
| warning | AI 生成声明：该临床摘要仅供审阅 |

### 4.9 治疗方案生成

**FR-15：治疗方案草案生成**

| 属性 | 内容 |
|------|------|
| 功能编号 | FR-15 |
| 功能描述 | 系统应基于医疗报告和推理路径生成治疗方案草案 |
| 输出格式 | JSON 结构，由 Treatment Plan Agent 生成 |

**输出必须包含字段**：

| 字段 | 说明 |
|------|------|
| options | 可能的治疗选项 |
| drug_candidates | 候选用药（可为空） |
| mechanism | 机制解释 |
| confidence | 置信度 |
| warnings | 限制说明：仅供临床决策支持，需经持证专业人员确认 |
| warning | 系统级 warning 标记 |

### 4.10 模型服务切换

**FR-16：模型服务配置化切换**

| 属性 | 内容 |
|------|------|
| 功能编号 | FR-16 |
| 功能描述 | 系统应支持通过环境变量配置切换模型服务，无需修改业务代码 |

**支持的模型服务**：

| 服务 | 配置方式 | 使用场景 |
|------|---------|----------|
| DeepSeek | `OPENAI_BASE_URL=https://api.deepseek.com` + `OPENAI_MODEL=deepseek-v4-flash` | 推理 |
| OpenAI 兼容 API | `OPENAI_BASE_URL=<任意兼容地址>` + `OPENAI_API_KEY` | 通用模型调用 |
| SGLang | `SGLANG_BASE_URL=http://localhost:30000` + `REASONING_ENGINE=sglang` | 自部署推理服务 |

**路由机制**：

- `ModelRouter.reason()` 根据 `REASONING_ENGINE` 选择引擎。
- `ModelRouter.generate()` 统一走 OpenAI SDK。
- 运行决策树中对应 reasoning 节点展示实际使用的引擎选项（llm_reasoner / deepseek_reasoner / sglang_reasoner）。

### 4.11 离线 Fallback

**FR-17：离线确定性 Fallback**

| 属性 | 内容 |
|------|------|
| 功能编号 | FR-17 |
| 功能描述 | 当未配置任何 API Key 时，系统应返回确定性 fallback 文本，保证全链路可运行 |

**Fallback 触发条件**：`OPENAI_API_KEY` 和 `DEEPSEEK_API_KEY` 均为空。

**Fallback 行为**：

| Agent 节点 | Fallback 输出 |
|-----------|-------------|
| supervisor | 固定返回 "deep-reasoning" |
| entity | 从 query 中提取 > 4 字符的单词作为实体 |
| medical_report | 返回固定 JSON 模板 |
| reasoning | 返回固定推理路径文本 |
| treatment_plan | 返回固定 JSON 模板（含 warning） |
| explain | 返回固定解释文本 |
| ranking | 排序操作（纯计算，不调模型） |
| retrieval | 图谱检索（纯计算，不调模型） |

### 4.12 Trace 回放

**FR-18：Trace 回放**

| 属性 | 内容 |
|------|------|
| 功能编号 | FR-18 |
| 功能描述 | 系统应提供 trace 回放接口，返回当前进程内 EventBus 已记录的全部事件 |
| 接口 | `GET /trace/replay` |
| 返回格式 | `{"events": [...]}` |

---

## 5. 界面原型

### 5.1 整体布局

系统前端采用左右分栏布局，左右比例为约 7:3。

```
┌─────────────────────────────────────────────────────────┐
│  MedReasonerAgent         [运行状态]                      │  <- 顶栏
├──────────────────────────────┬──────────────────────────┤
│                              │                          │
│     对话式通信面板            │     运行决策树            │
│     (ConversationPanel)     │     (AgentGraph)         │
│                              │                          │
│  ┌─────────────────────┐    │  ┌──────────────────┐    │
│  │ Bot 图标             │    │  │  意图分类         │    │
│  │ 医疗多 Agent 工作区   │    │  │  ○ 简单 ○ 多步 ● 深度 │
│  │ 输入医疗推理问题...   │    │  │       │            │    │
│  └─────────────────────┘    │  │  实体抽取         │    │
│                              │  │  ○ 抽取 ○ 规范 ● 症状 │
│  ┌─────────────────────┐    │  │       │            │    │
│  │ User: 患者胸痛发热...│    │  │  病例理解         │    │
│  └─────────────────────┘    │  │  ...               │    │
│  ┌─────────────────────┐    │  └──────────────────┘    │
│  │ Supervisor Agent    │    │                          │
│  │ 已完成本步骤...     │    │                          │
│  │ ▶ 查看内部传递内容  │    │                          │
│  └─────────────────────┘    │                          │
│                              │                          │
├──────────────────────────────┴──────────────────────────┤
│  [语言选择 ▾]  [___________________________] [发送 ▶]   │  <- 输入区
└─────────────────────────────────────────────────────────┘
```

### 5.2 对话面板

组件路径：[frontend/components/ConversationPanel.tsx](frontend/components/ConversationPanel.tsx)

**空状态原型**：

```
        ┌────────────────────────────────┐
        │                                │
        │         🤖 (Bot 图标)          │
        │    医疗多 Agent 工作区          │
        │  输入医疗推理问题后，你会看到    │
        │  面向用户的解释；Agent 间传递    │
        │  的内部上下文会折叠在详情中。    │
        │                                │
        └────────────────────────────────┘
```

**消息气泡原型（用户消息）**：

```
                                          ┌─────────────────────────┐
                                          │ 用户                    │
                                          │ 患者胸痛、发热，有糖尿   │
                                          │ 病风险和炎症指标异常。   │
                              👤 (用户图标) └─────────────────────────┘
```

**消息气泡原型（Agent 消息）**：

```
┌──────────────────────────────────────────────────────────┐
│ 🤖 (Bot 图标)                                            │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ Entity Agent                                         │ │
│ │                                                      │ │
│ │ **Entity Agent** 已完成本步骤，使用了 **entity_extractor**。│
│ │ 系统从你的描述中提取了关键医学概念。                      │ │
│ │                                                      │ │
│ │ **结果摘要：** 胸痛, 发热, 糖尿病, 炎症                 │ │
│ │                                                      │ │
│ │ ▶ 查看 Agent 内部传递内容                              │ │
│ └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

**最终答案消息原型（System 消息）**：

```
┌──────────────────────────────────────────────────────────┐
│ 🤖 (Bot 图标)                                            │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ 最终回复                                             │ │
│ │                                                      │ │
│ │ 根据您的描述，系统分析了胸痛、发热、糖尿病风险          │ │
│ │ 和炎症指标异常等关键医学概念，通过 DRG 知识图谱        │ │
│ │ 检索了相关疾病关联...(Markdown 渲染)                   │ │
│ │                                                      │ │
│ │ ⚠️ AI 生成说明：本输出仅为临床决策支持演示...         │ │
│ └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

**输入区域原型**：

```
┌──────────────────────────────────────────────────────────┐
│                           Agent 语言 [中文 ▾]             │
│ ┌──────────────────────────────────────────────────┐ ┌─┐ │
│ │ 输入医疗推理问题...                              │ │▶│ │
│ │                                                  │ │ │ │
│ │                                                  │ └─┘ │
│ └──────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────┘
```

### 5.3 运行决策树面板

组件路径：[frontend/components/AgentGraph.tsx](frontend/components/AgentGraph.tsx)

**整体结构**：右侧窄列，React Flow 画布，带 Controls 和 Background。

**单层决策节点结构**：

```
              ┌──────────┐
              │ ✓ 意图分类 │  <- DecisionNode（绿色边框=已完成）
              └─────┬────┘
         ┌──────────┼──────────┐
         ▼          ▼          ▼
    ┌─────────┐ ┌──────────┐ ┌──────────┐
    │ 简单回答 │ │ 多步推理  │ │● 深度推理 │  <- OptionNode（绿色=选中）
    └─────────┘ └──────────┘ └─────┬────┘
                                    │
                                    ▼
                              ┌──────────┐
                              │ ◉ 实体抽取 │  <- DecisionNode（橙色边框=active）
                              └──────────┘
```

**多层级完整执行路径示意**：

```
                 ┌──────────┐
                 │ ✓ 意图分类 │  (green)
                 └─────┬────┘
            ┌──────────┼──────────┐
            ▼          ▼          ▼
       ┌─────────┐ ┌──────────┐ ┌──────────┐
       │ 简单回答 │ │ 多步推理  │ │● 深度推理 │  (green)
       └─────────┘ └──────────┘ └─────┬────┘
                                       │
                                       ▼
                                 ┌──────────┐
                                 │ ✓ 实体抽取 │  (green)
                                 └─────┬────┘
                            ┌──────────┼──────────┐
                            ▼          ▼          ▼
                       ┌─────────┐ ┌──────────┐ ┌──────────┐
                       │提取关键词│ │● 规范术语 │ │ 识别症状  │  (green)
                       └─────────┘ └─────┬────┘ └──────────┘
                                          │
                                          ▼
                                    ┌──────────┐
                                    │ ✓ 病例理解 │  (green)
                                    └─────┬────┘
                               ┌──────────┼──────────┐
                               ▼          ▼          ▼
                          ┌─────────┐ ┌──────────┐ ┌──────────┐
                          │整理摘要  │ │ 分析风险 │ │● 估计严重 │  (green)
                          └─────────┘ └──────────┘ └─────┬────┘
                                                          │
                                                          ▼
                                                    ┌──────────┐
                                                    │ ✓ DRG检索 │  (green)
                                                    └─────┬────┘
                                              (继续向下延伸...)
                                                          │
                                                          ▼
                                                    ┌──────────┐
                                                    │ ◉ 医学推理 │  (orange - active)
                                                    └──────────┘
                                               ┌─────────────────┐
                                         (等待执行完成后显示候选)
```

**图例**：

| 符号 | 含义 |
|------|------|
| ✓ 绿色决策节点 | 已完成 |
| ◉ 橙色决策节点 | 正在执行（带旋转动画） |
| ⬠ 灰色决策节点 | 等待执行 |
| ● 绿色候选节点 | 实际选中 |
| ○ 灰色候选节点 | 未选中 |
| ── 灰色边 | 未执行路径 |
| ── 绿色边 | 实际执行路径 |
| ╌╌ 动画虚线 | 当前激活路径 |

### 5.4 Trace 面板

组件路径：[frontend/components/TracePanel.tsx](frontend/components/TracePanel.tsx)

**功能描述**：以列表形式展示每个 Agent 的执行状态和最近事件日志。

**状态指示**：

| 状态 | 显示 | 含义 |
|------|------|------|
| WAIT | 灰色圆点 | 尚未执行 |
| RUNNING | 橙色旋转圆点 | 正在执行 |
| OK | 绿色对勾 | 已完成 |

### 5.5 报告卡片

组件路径：[frontend/components/ReportCard.tsx](frontend/components/ReportCard.tsx)

**功能描述**：当 medical_report 可用时，以卡片形式展示结构化病例理解内容。

```
┌──────────────────────────────────────────┐
│  📋 医疗报告                             │
│                                          │
│  可能疾病：需临床确认                     │
│  症状：胸痛、发热                        │
│  风险因素：糖尿病                        │
│  临床解释：初步 AI 辅助病例摘要           │
│  严重程度估计：待定                       │
│                                          │
│  ⚠️ AI-generated clinical summary        │
│     for review only.                     │
└──────────────────────────────────────────┘
```

### 5.6 治疗卡片

组件路径：[frontend/components/TreatmentCard.tsx](frontend/components/TreatmentCard.tsx)

**功能描述**：当 treatment_plan 可用时，以卡片形式展示治疗方案草案。

```
┌──────────────────────────────────────────┐
│  💊 治疗方案草案                         │
│                                          │
│  治疗选项：...                           │
│  候选用药：...                           │
│  机制解释：...                           │
│  置信度：低                              │
│                                          │
│  ⚠️ For clinical decision support only;  │
│     confirm with licensed professionals. │
└──────────────────────────────────────────┘
```

### 5.7 交互状态说明

| 状态 | 顶栏状态 | 发送按钮 | 运行树 | 对话区 |
|------|---------|---------|--------|--------|
| **就绪** | 显示"就绪" | 可用 | 显示"等待输入" | 空状态或上次结果 |
| **运行中** | 显示"多 Agent 推理中" | 禁用（变灰） | 实时更新，当前节点高亮 | 逐步新增 Agent 消息 |
| **完成** | 恢复"就绪" | 可用 | 完整执行路径（绿色） | 显示最终答案 |
| **错误** | 恢复"就绪" | 可用 | 保留已执行部分 | 可能显示错误提示 |

---

## 6. 非功能需求

### 6.1 性能需求

| 编号 | 需求 | 指标 |
|------|------|------|
| NFR-01 | WebSocket 事件延迟 | 单个 Agent 执行完成后 100ms 内事件到达前端 |
| NFR-02 | 前端渲染帧率 | 运行树更新时不低于 30fps |
| NFR-03 | API 超时 | 同步 `/run` 接口超时上限 120s |
| NFR-04 | 内存占用 | 单次推理 trace 在内存中保留不超过 1000 条事件 |

### 6.2 可用性需求

| 编号 | 需求 | 指标 |
|------|------|------|
| NFR-05 | 界面语言 | 支持中文和英文切换 |
| NFR-06 | Markdown 渲染 | 用户可见消息支持 Markdown（标题、列表、加粗、代码块等） |
| NFR-07 | 内部信息折叠 | 默认折叠，需要时可展开；展开/折叠无明显延迟 |
| NFR-08 | 空状态引导 | 首次使用显示引导文案 |

### 6.3 可靠性需求

| 编号 | 需求 | 指标 |
|------|------|------|
| NFR-09 | 离线可运行 | 无 API Key 时系统仍能跑通全链路 |
| NFR-10 | WebSocket 断连 | 前端显示错误状态，可重新连接 |
| NFR-11 | 模型调用失败 | 不阻断整体链路，记录错误并继续 |
| NFR-12 | 输入校验 | 空 query 不可提交，WebSocket 模式下返回 error 事件 |

### 6.4 可维护性需求

| 编号 | 需求 | 指标 |
|------|------|------|
| NFR-13 | 模块化 | 严格按 API、Graph、Runtime、Agent、KG、Tools、Frontend 分层 |
| NFR-14 | 代码约定 | Python 3.10+、TypeScript、遵循项目目录结构 |
| NFR-15 | 配置外部化 | 所有模型配置通过 `.env` 管理 |
| NFR-16 | 日志记录 | trace 机制记录所有 Agent 执行步骤 |

### 6.5 可扩展性需求

| 编号 | 需求 | 指标 |
|------|------|------|
| NFR-17 | 模型扩展 | 新增模型服务仅需扩展 `ModelRouter` 和 `.env` |
| NFR-18 | Agent 扩展 | 新增 Agent 仅需实现函数并在 workflow 中添加节点 |
| NFR-19 | 图谱扩展 | DRG 图谱可替换为真实数据源，保持接口不变 |
| NFR-20 | 决策策略扩展 | `DecisionPolicy` 可替换为基于模型的路由策略 |

### 6.6 安全需求

| 编号 | 需求 | 指标 |
|------|------|------|
| NFR-21 | 密钥安全 | `.env` 不提交到 Git |
| NFR-22 | 前端依赖 | `npm audit` 无已知漏洞 |
| NFR-23 | 输出安全 | 所有医疗输出必须包含 warning 和免责声明 |
| NFR-24 | 数据安全 | 不保存真实患者隐私数据 |

---

## 7. 数据需求

### 7.1 全局状态数据模型

`DRGState` 是系统中所有 Agent 共享的数据结构：

| 字段名 | 类型 | 默认值 | 写入者 | 说明 |
|--------|------|--------|--------|------|
| query | str | "" | API（初始化） | 用户输入的自然语言 query |
| language | str | "zh" | API（初始化） | 输出语言，"zh" 或 "en" |
| entities | List[str] | [] | entity Agent | 抽取的医学实体列表 |
| subgraph | dict | {} | retrieval Agent | DRG 子图，含 nodes、edges、hops |
| reasoning_paths | List[Any] | [] | reasoning Agent | 医学推理路径列表 |
| ranked_paths | List[Any] | [] | ranking Agent | 排序后的推理路径 |
| medical_report | dict | {} | medical_report Agent | 结构化病例理解，含 text 和 warning |
| treatment_plan | dict | {} | treatment_plan Agent | 治疗方案草案，含 text 和 warning |
| answer | str | "" | explain Agent | 最终自然语言解释 |
| plan | dict | {} | supervisor Agent | 执行计划，含 mode 字段 |
| trace | List[dict] | [] | 各 Agent（通过 append_trace） | 执行轨迹，每条为 {node, output} |

### 7.2 事件数据模型

EventBus 中传递的事件对象字段：

| 字段名 | 类型 | 说明 | 出现于 |
|--------|------|------|--------|
| event | str | 事件类型：node_start / node_end / complete / error | 全部 |
| node | str | 当前 Agent 名称 | node_start / node_end |
| timestamp | float | UTC 时间戳 | 全部 |
| decision_id | str | 决策节点 ID（等同 node 名） | node_start / node_end |
| parent_decision_id | str\|null | 父决策节点 ID | node_start / node_end |
| decision_options | List[str] | 候选决策选项 | node_start / node_end |
| selected_option | str | 实际选中选项 | node_end |
| selected_tool | str | 实际选中工具（同 selected_option） | node_end |
| output | Any | Agent 节点输出 | node_end |
| available_tools | List[str] | 可用工具列表（同 decision_options） | node_start / node_end |
| state | dict | 当前 state snapshot | node_start / node_end / complete |
| answer | str | 最终答案 | complete |
| trace | List[dict] | 完整执行轨迹 | complete |

### 7.3 前端状态数据模型

`traceStore`（Zustand store）管理的前端状态字段：

| 字段名 | 类型 | 初始值 | 说明 |
|--------|------|--------|------|
| events | TraceEvent[] | [] | 所有接收到的事件 |
| messages | ChatMessage[] | [] | 聊天消息列表 |
| language | "zh" \| "en" | "zh" | 当前语言 |
| activeNode | string \| null | null | 当前执行的节点名 |
| decisionSequence | string[] | [] | 决策节点执行顺序 |
| completedNodes | string[] | [] | 已完成节点列表 |
| selectedTools | Record<string, string> | {} | 各节点的选中工具 |
| availableTools | Record<string, string[]> | {} | 各节点的可用工具列表 |
| decisionParents | Record<string, string \| null> | {} | 决策节点父子关系 |
| finalState | Record<string, unknown> | {} | 最终 state |
| answer | string | "" | 最终答案文本 |

**ChatMessage 结构**：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 消息唯一 ID |
| role | "user" \| "agent" \| "system" | 消息来源角色 |
| title | string | 消息标题（Agent 名称或"用户"/"最终回复"） |
| content | string | 面向用户的消息正文（Markdown） |
| details | string? | 内部详情（可选，用于折叠区） |
| node | string? | 对应的 Agent 节点名（可选） |

### 7.4 知识图谱数据模型

**边结构**（DRG 图谱三元组）：

| 字段 | 类型 | 说明 |
|------|------|------|
| source | str | 源节点名称 |
| relation | str | 关系类型 |
| target | str | 目标节点名称 |

**关系类型枚举**：

| 关系类型 | 含义 |
|----------|------|
| suggests | 症状提示疾病 |
| mapped_to | 疾病映射到 DRG 分组 |
| treated_by | 疾病治疗方式 |
| increases_risk_of | 风险因素增加疾病概率 |
| confirms_or_rules_out | 检查项目确定/排除疾病 |

**子图结构**：

| 字段 | 类型 | 说明 |
|------|------|------|
| nodes | List[str] | 子图包含的节点名称列表 |
| edges | List[dict] | 子图包含的边列表 |
| hops | int | 检索跳数 |

---

## 8. 外部接口需求

### 8.1 HTTP API 接口

#### 8.1.1 Health Check

| 属性 | 内容 |
|------|------|
| 方法 | GET |
| 路径 | `/health` |
| 请求体 | 无 |
| 成功响应 | `200 OK`，`{"status": "ok"}` |

#### 8.1.2 Run（同步）

| 属性 | 内容 |
|------|------|
| 方法 | POST |
| 路径 | `/run` |
| Content-Type | application/json |
| 请求体 | `{"query": "...", "language": "zh"}` |
| 成功响应 | `200 OK`，`{"answer": "...", "trace": [...], "medical_report": {...}, "treatment_plan": {...}, "state": {...}}` |
| 说明 | 同步执行完整 LangGraph 工作流，阻塞直到完成 |

#### 8.1.3 Trace Replay

| 属性 | 内容 |
|------|------|
| 方法 | GET |
| 路径 | `/trace/replay` |
| 请求体 | 无 |
| 成功响应 | `200 OK`，`{"events": [...]}` |
| 说明 | 返回当前进程内 EventBus 已记录的全部事件 |

### 8.2 WebSocket 接口

#### 8.2.1 Run Streaming

| 属性 | 内容 |
|------|------|
| 协议 | WebSocket |
| 路径 | `/ws/run` |
| 客户端发送 | `{"query": "...", "language": "en"}` |
| 服务端事件流 | node_start -> node_end -> ... -> complete |

**WebSocket 事件序列示例**：

```
1. node_start (supervisor)
2. node_end (supervisor) -> selected_option: deep-reasoning
3. node_start (entity)
4. node_end (entity) -> selected_option: entity_extractor
5. node_start (medical_report)
6. node_end (medical_report) -> selected_option: case_summarizer
7. node_start (retrieval)
8. node_end (retrieval) -> selected_option: direct_drg_lookup
9. node_start (reasoning)
10. node_end (reasoning) -> selected_option: llm_reasoner
11. node_start (ranking)
12. node_end (ranking) -> selected_option: path_ranker
13. node_start (treatment_plan)
14. node_end (treatment_plan) -> selected_option: treatment_generator
15. node_start (explain)
16. node_end (explain) -> selected_option: plain_language_explainer
17. complete -> answer, trace, state
```

**错误处理**：
- query 为空：立即发送 `{"event": "error", "message": "query is required"}`
- WebSocket 断开：前端以 error 事件处理

### 8.3 环境变量契约

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| OPENAI_API_KEY | 否 | — | OpenAI 或兼容 API 的密钥 |
| DEEPSEEK_API_KEY | 否 | — | DeepSeek API 密钥（也用作 OPENAI_API_KEY 备选） |
| OPENAI_BASE_URL | 否 | — | OpenAI 兼容 API 的服务地址 |
| OPENAI_MODEL | 否 | gpt-4o-mini | 默认使用的模型名称 |
| LLM_TEMPERATURE | 否 | 0.2 | 模型推理温度 |
| REASONING_ENGINE | 否 | sglang | 推理引擎选择：llm / sglang |
| SGLANG_BASE_URL | 否 | — | SGLang 推理服务地址 |
| SGLANG_MODEL | 否 | default | SGLang 模型名称 |
| NEXT_PUBLIC_API_BASE | 否 | http://localhost:8000 | 前端连接的后端 API 地址 |

### 8.4 Markdown 展示契约

用户可见的 Agent 输出必须以 Markdown 格式组织，由前端 Markdown renderer 渲染。

**要求**：
- Agent 输出的面向用户部分应为自然语言 Markdown 字符串。
- 前端使用 `MarkdownMessage` 组件渲染 Markdown 内容。
- 内部原始数据（JSON、trace 对象等）不得直接出现在 Markdown 渲染区，必须放入折叠区。

---

## 9. 体系结构约束

### 9.1 总体架构

系统采用前后端分离的分层架构：

```
┌──────────────────────────────────────────┐
│                用户浏览器                  │
├──────────────────────────────────────────┤
│           Next.js 前端应用                │
│  ┌──────────┬──────────┬──────────────┐  │
│  │对话面板   │运行树    │ Trace/Report │  │
│  └──────────┴──────────┴──────────────┘  │
│  ┌──────────┬──────────────────────────┐  │
│  │traceStore│ WebSocket / HTTP Client  │  │
│  └──────────┴──────────────────────────┘  │
├──────────────────────────────────────────┤
│        WebSocket / HTTP (JSON)            │
├──────────────────────────────────────────┤
│           FastAPI 后端服务                │
│  ┌────────────────────────────────────┐  │
│  │            API Layer (app.py)      │  │
│  ├────────────────────────────────────┤  │
│  │          Graph Layer (graph/)      │  │
│  ├────────────────────────────────────┤  │
│  │         Runtime Layer (runtime/)   │  │
│  │  ┌──────────┬──────────┬────────┐  │  │
│  │  │Executor   │EventBus   │Router  │  │  │
│  │  └──────────┴──────────┴────────┘  │  │
│  ├────────────────────────────────────┤  │
│  │          Agent Layer (agents/)     │  │
│  │  ┌────┬────┬────┬────┬────┬────┐  │  │
│  │  │Sup │Ent │Med │Ret │Rea │Rnk │  │  │
│  │  │    │    │Rpt │    │    │    │  │  │
│  │  └────┴────┴────┴────┴────┴────┘  │  │
│  │  ┌──────────┬──────────┐          │  │
│  │  │Treatment │Explain   │          │  │
│  │  └──────────┴──────────┘          │  │
│  ├────────────────────────────────────┤  │
│  │         KG Layer (kg/)             │  │
│  │         Tools Layer (tools/)       │  │
│  ├────────────────────────────────────┤  │
│  │     LLM / SGLang / DeepSeek API    │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

### 9.2 模块划分

| 层 | 目录/文件 | 职责 |
|------|-----------|------|
| API | `app.py` | HTTP 路由、WebSocket 端点、状态初始化 |
| Graph | `graph/state.py` | 全局状态类型定义 |
| Graph | `graph/workflow.py` | LangGraph 节点和边定义、工作流编译 |
| Runtime | `runtime/executor.py` | 统一节点执行包装、事件触发 |
| Runtime | `runtime/event_bus.py` | 发布/订阅事件总线 |
| Runtime | `runtime/decision_policy.py` | 决策候选和选中策略生成 |
| Runtime | `runtime/router.py` | 模型路由（LLM vs SGLang） |
| Agent | `agents/supervisor.py` | 意图分类 Agent |
| Agent | `agents/entity.py` | 实体抽取 Agent |
| Agent | `agents/medical_report.py` | 病例报告 Agent |
| Agent | `agents/retrieval.py` | DRG 检索 Agent |
| Agent | `agents/reasoning.py` | 医学推理 Agent |
| Agent | `agents/ranking.py` | 路径排序 Agent |
| Agent | `agents/treatment_plan.py` | 治疗方案 Agent |
| Agent | `agents/explain.py` | 解释生成 Agent |
| KG | `kg/drg_loader.py` | DRG 图谱数据加载 |
| KG | `kg/query.py` | 图谱子图查询 |
| Tools | `tools/llm.py` | LLM API 调用封装 |
| Tools | `tools/sglang_client.py` | SGLang API 调用封装 |
| Tools | `tools/trace.py` | trace 记录辅助函数 |
| Frontend | `frontend/app/` | Next.js 页面 |
| Frontend | `frontend/components/` | UI 组件 |
| Frontend | `frontend/store/` | Zustand 状态管理 |
| Frontend | `frontend/lib/` | API 和 WebSocket 客户端 |

### 9.3 设计原则

| 原则 | 实现方式 |
|------|---------|
| **抽象** | 抽象出 State、Agent、Event、Decision 等核心概念 |
| **关注点分离** | Executor 管生命周期，DecisionPolicy 管决策，Agent 管业务，Store 管状态 |
| **模块化** | 按 API / Graph / Runtime / Agent / KG / Tools / Frontend 分层 |
| **信息隐蔽** | 内部 Agent trace 折叠，不直接暴露给用户 |
| **功能独立** | 每个 Agent 只承担单一推理步骤 |
| **高内聚低耦合** | Agent 间仅通过 State 通信，无直接依赖 |
| **数据/控制/展示分离** | State（数据）、LangGraph（控制）、React（展示）三层独立 |

### 9.4 技术约束

| 约束项 | 要求 |
|--------|------|
| 后端语言 | Python >= 3.10 |
| 后端框架 | FastAPI |
| 工作流编排 | LangGraph |
| LLM SDK | OpenAI Python SDK |
| 前端框架 | Next.js (App Router) |
| 前端语言 | TypeScript |
| 图谱可视化 | React Flow (@xyflow/react) |
| 状态管理 | Zustand |
| 图标库 | Lucide React |
| 浏览器支持 | 现代 Chromium / Safari / Firefox |
| Python 环境 | Conda environment `myenv` |
| 包管理 | pip (Python)、npm (Node.js) |

---

## 10. 医疗安全与伦理约束

### 10.1 系统定位声明

MedReasonerAgent 是**医疗推理原型和临床决策支持演示系统**，不是医疗器械，不是诊断系统，不提供医疗建议。

系统必须在以下位置明确展示定位声明：

- 最终答案中
- medical report 输出中
- treatment plan 输出中
- UI 空状态引导文案中

### 10.2 禁止行为

| 编号 | 禁止行为 | 实施方式 |
|------|----------|----------|
| SB-01 | 声称给出最终诊断 | prompt 中指示 LLM 避免确定性诊断表述 |
| SB-02 | 直接开具处方 | treatment_plan 的 drug_candidates 字段标明仅供参考 |
| SB-03 | 替代医生判断 | 所有输出提示"需经持证专业人员确认" |
| SB-04 | 鼓励用户延误就医 | prompt 中包含"紧急情况应寻求即时医疗服务" |
| SB-05 | 对急症给出确定性居家处理建议 | severity_estimation 高时，输出中强调就医建议 |

### 10.3 必须提示内容

| 编号 | 必须提示 | 位置 |
|------|----------|------|
| MR-01 | "AI-generated clinical summary for review only" | medical_report |
| MR-02 | "For clinical decision support only; confirm with licensed professionals" | treatment_plan |
| MR-03 | 使用用户友好语言，包含医疗限制说明 | explain（最终答案） |
| MR-04 | 仅用于学习、研究和原型验证 | 系统整体声明 |

### 10.4 数据安全

| 编号 | 安全要求 | 实现 |
|------|----------|------|
| DS-01 | `.env` 不提交 | `.gitignore` 包含 `.env` |
| DS-02 | API Key 不出现在前端代码中 | 所有模型调用走后端 |
| DS-03 | 不保存真实患者隐私数据 | 系统无持久化存储 |
| DS-04 | 示例输入避免可识别个人信息 | 使用脱敏示例 |

### 10.5 模型风险管理

**已知模型风险**：

| 风险 | 说明 | 缓解措施 |
|------|------|----------|
| 幻觉 | 模型可能生成不存在的医学术语或关联 | 输出 warning；保留 trace 供审查 |
| 不完整推理 | 模型可能跳过关键推理步骤 | trace 机制保留全链路信息 |
| 错误医学建议 | 模型可能给出有害建议 | 所有治疗输出含"需临床确认"警告 |
| 过度自信 | 模型可能以确定性语气输出 | prompt 中指示使用谨慎措辞 |

**后续升级方向**：
- 加入幻觉评估 Agent
- 加入安全输出过滤 Agent
- 加入医学知识一致性校验

### 10.6 伦理边界

系统在设计和使用中应遵循以下伦理边界：

1. **透明性**：系统始终明确标识 AI 生成内容。
2. **可审查性**：所有推理步骤可通过 trace 回溯。
3. **非替代性**：系统是辅助工具，不能替代医生判断。
4. **研究目的**：系统仅用于学习、研究和原型验证。
5. **紧急情况**：紧急医疗需求应寻求即时专业医疗服务。

---

## 11. 测试与验收

### 11.1 测试策略

系统测试分为四个层面：

```
验收测试（端到端场景验证）
    ^
集成测试（前后端联调、WebSocket 事件流）
    ^
模块测试（Agent 单元测试、API 接口测试）
    ^
静态检查（构建、安全审计、代码规范）
```

### 11.2 后端测试用例

| 用例编号 | 测试项 | 测试方法 | 预期结果 |
|----------|--------|----------|----------|
| BT-01 | Health Check | `GET /health` | `{"status": "ok"}` |
| BT-02 | 同步 Run（中文） | `POST /run` with `{"query":"患者胸痛发热","language":"zh"}` | HTTP 200, 返回 answer, trace, medical_report, treatment_plan |
| BT-03 | 同步 Run（英文） | `POST /run` with `{"query":"patient has chest pain","language":"en"}` | HTTP 200, 返回结果 |
| BT-04 | Trace 节点完整性 | 检查 BT-02 返回的 trace | 含 supervisor, entity, medical_report, retrieval, reasoning, ranking, treatment_plan, explain |
| BT-05 | Trace Replay | `GET /trace/replay` | 返回 events 数组 |
| BT-06 | WebSocket Streaming | 通过 WebSocket 客户端发送 query | 接收 node_start 和 node_end 事件序列 |
| BT-07 | WebSocket Complete 事件 | 执行完成 | 接收到 complete 事件，含 answer 和 trace |
| BT-08 | WebSocket 空 query | 发送 `{"query":"","language":"zh"}` | 收到 error 事件 |
| BT-09 | Offline Fallback | 清空所有 API Key 后执行 | 仍返回 HTTP 200，trace 完整 |

### 11.3 前端测试用例

| 用例编号 | 测试项 | 测试方法 | 预期结果 |
|----------|--------|----------|----------|
| FT-01 | 构建测试 | `npm run build` | 构建成功，无错误 |
| FT-02 | 安全审计 | `npm audit` | found 0 vulnerabilities |
| FT-03 | 输入 query | 在输入框输入文字并点击发送 | 对话区显示用户消息 |
| FT-04 | 语言切换 | 切换语言选择器 | Agent 输出语言随之改变 |
| FT-05 | Agent 消息渲染 | 执行推理 | 每条 Agent 消息以 Markdown 渲染 |
| FT-06 | 内部信息折叠 | 点击"查看 Agent 内部传递内容" | 展开原始输出和上下文摘要 |
| FT-07 | 运行树纵向布局 | 执行推理 | 决策节点从上到下排列 |
| FT-08 | 运行树水平候选 | 存在候选选项时 | 同层候选水平排列 |
| FT-09 | 未执行层级不显示 | 执行初期 | 仅显示已发生的决策层级 |
| FT-10 | 执行路径颜色 | 执行完成 | 实际执行路径为绿色 |
| FT-11 | 空状态显示 | 首次加载页面 | 显示引导文案 |
| FT-12 | 运行中按钮状态 | 执行期间 | 发送按钮禁用 |

### 11.4 模型配置测试

| 用例编号 | 配置 | 预期结果 |
|----------|------|----------|
| MT-01 | DeepSeek 配置 | 模型调用成功，REASONING_ENGINE=llm |
| MT-02 | SGLang 配置 | reasoning 使用 SGLang endpoint |
| MT-03 | Offline fallback | 全链路跑通，无外部 API 调用 |
| MT-04 | 模型切换 | 运行树中 reasoning 决策节点显示对应引擎选项 |

### 11.5 验收标准

系统验收通过需满足以下全部条件：

**后端验收**：

- [ ] `GET /health` 返回 `{"status": "ok"}`
- [ ] `POST /run` 返回 HTTP 200，包含 answer、trace、medical_report、treatment_plan
- [ ] trace 包含全部 8 个 Agent 节点的执行记录
- [ ] WebSocket streaming 可正常推送事件序列
- [ ] trace replay 接口可正常返回历史事件

**前端验收**：

- [ ] `npm run build` 构建成功
- [ ] `npm audit` 返回 0 vulnerabilities
- [ ] 页面可输入 query 并启动执行
- [ ] Agent 消息默认以自然语言 Markdown 展示
- [ ] 内部上下文默认折叠，可手动展开
- [ ] 运行树随 WebSocket 事件实时更新
- [ ] 运行树布局符合"纵向排列、水平候选"规则
- [ ] 只有实际执行路径显示为绿色

**安全与配置验收**：

- [ ] `.env` 不进入 Git 版本控制
- [ ] `.env.example` 保留配置模板
- [ ] 所有医疗输出包含 warning 或免责声明
- [ ] 离线 fallback 模式下全链路可运行

---

## 12. 运行环境与部署

### 12.1 推荐运行环境

| 组件 | 要求 |
|------|------|
| 操作系统 | macOS / Linux / Windows (WSL) |
| Python | >= 3.10 |
| Conda | 推荐使用 Conda 环境 `myenv` |
| Node.js | >= 18 |
| npm | >= 9 |
| 浏览器 | Chromium 100+ / Safari 16+ / Firefox 120+ |
| Python 依赖 | fastapi, uvicorn, langgraph, openai, httpx, python-dotenv, pydantic |
| Node 依赖 | next, react, react-dom, @xyflow/react, zustand, lucide-react |

### 12.2 后端运行

```bash
cd /Users/zym/Documents/Code/Program/Agent/MedReasonerAgent
conda activate myenv
pip install -r requirements.txt
uvicorn app:app --reload
```

后端默认地址：`http://127.0.0.1:8000`

### 12.3 前端运行

```bash
cd /Users/zym/Documents/Code/Program/Agent/MedReasonerAgent/frontend
conda activate myenv
npm install
npm run dev
```

前端默认地址：`http://localhost:3000`

### 12.4 配置文件说明

- `.env`：本地配置，包含 API Key 等敏感信息，不提交到 Git。
- `.env.example`：配置模板文件，提交到 Git，供协作者参考。
- `.gitignore`：忽略 `.env`、`node_modules/`、`.next/`、`__pycache__/` 等。

---

## 13. 约束与假设

### 13.1 技术约束

| 编号 | 约束 | 影响 |
|------|------|------|
| TC-01 | LangGraph 工作流当前为固定线性拓扑 | 不支持条件分支和循环 |
| TC-02 | EventBus 为进程内实现 | 不支持多进程/分布式事件广播 |
| TC-03 | DRG 图谱为内存加载 | 不支持大规模知识和持久化 |
| TC-04 | 无会话隔离 | 多用户并发时事件混在一起 |
| TC-05 | 依赖外部 LLM API | 服务可用性受外部影响 |
| TC-06 | DecisionPolicy 为规则式 | 不支持基于模型推理的决策 |

### 13.2 业务约束

| 编号 | 约束 | 说明 |
|------|------|------|
| BC-01 | 非医疗设备 | 系统不得用于真实临床诊断 |
| BC-02 | 非生产系统 | 系统为原型级别，不保证生产级可靠性 |
| BC-03 | 无数据持久化 | 不保存用户数据和执行历史 |

### 13.3 假设条件

| 编号 | 假设 | 说明 |
|------|------|------|
| AS-01 | 用户理解系统为原型 | 用户不会将系统输出作为医疗决策依据 |
| AS-02 | 网络连通性 | 使用外部模型时需要网络连接 |
| AS-03 | 单用户使用 | 当前阶段假设单用户操作模式 |
| AS-04 | 示例输入合理 | 用户输入为典型医疗查询，不含恶意内容 |

---

## 14. 附录

### 附录 A：模块目录结构

```
MedReasonerAgent/
├── app.py                         # FastAPI 入口
├── requirements.txt               # Python 依赖
├── README.md                      # 项目说明
├── .env.example                   # 配置模板
├── .gitignore                     # Git 忽略规则
├── docs/
│   ├── requirements.md            # 原需求文档
│   ├── requirements-writing-logic.md  # 需求文档撰写逻辑
│   ├── complete-requirements-analysis.md  # 本文档
│   └── coursework/                # 课程作业文档
│       ├── 01-user-requirements.md
│       ├── 02-software-requirements-specification.md
│       ├── 03-architecture-design.md
│       ├── 04-interface-contracts.md
│       ├── 05-safety-and-ethics.md
│       └── 06-test-and-acceptance.md
├── graph/
│   ├── state.py                   # DRGState 定义
│   └── workflow.py                # LangGraph 工作流编译
├── runtime/
│   ├── __init__.py
│   ├── executor.py                # 节点执行包装器
│   ├── event_bus.py               # 事件总线
│   ├── decision_policy.py         # 决策策略
│   └── router.py                  # 模型路由器
├── agents/
│   ├── supervisor.py              # 意图分类 Agent
│   ├── planner.py                 # 计划 Agent（保留）
│   ├── entity.py                  # 实体抽取 Agent
│   ├── medical_report.py          # 病例报告 Agent
│   ├── retrieval.py               # DRG 检索 Agent
│   ├── reasoning.py               # 医学推理 Agent
│   ├── ranking.py                 # 路径排序 Agent
│   ├── treatment_plan.py          # 治疗方案 Agent
│   └── explain.py                 # 解释生成 Agent
├── kg/
│   ├── drg_loader.py              # DRG 图谱加载
│   └── query.py                   # 图谱查询
├── tools/
│   ├── llm.py                     # LLM API 封装
│   ├── sglang_client.py           # SGLang API 封装
│   └── trace.py                   # Trace 工具
└── frontend/
    ├── package.json
    ├── tsconfig.json
    ├── next-env.d.ts
    ├── app/
    │   ├── layout.tsx             # 根布局
    │   └── page.tsx               # 主页面
    ├── components/
    │   ├── AgentGraph.tsx          # 运行决策树
    │   ├── ConversationPanel.tsx   # 对话面板
    │   ├── MarkdownMessage.tsx     # Markdown 渲染
    │   ├── NodeCard.tsx            # 节点卡片
    │   ├── ReportCard.tsx          # 报告卡片
    │   ├── TracePanel.tsx          # Trace 面板
    │   └── TreatmentCard.tsx       # 治疗卡片
    ├── lib/
    │   ├── api.ts                  # HTTP API 客户端
    │   └── websocket.ts            # WebSocket 客户端
    └── store/
        └── traceStore.ts           # Zustand 状态管理
```

### 附录 B：环境变量完整列表

```env
# OpenAI / DeepSeek 兼容 API
OPENAI_API_KEY=
DEEPSEEK_API_KEY=
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-flash
LLM_TEMPERATURE=0.2

# 推理引擎选择 (llm / sglang)
REASONING_ENGINE=llm

# SGLang 推理服务
SGLANG_BASE_URL=
SGLANG_MODEL=default

# 前端 API 地址
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

### 附录 C：Agent 节点职责速查表

| 顺序 | 节点名 | 中文名 | 写入字段 | 候选选项 | 依赖 |
|------|--------|--------|----------|----------|------|
| 0 | supervisor | 意图分类 | plan | simple, multi-hop, deep-reasoning | query |
| 1 | entity | 实体抽取 | entities | entity_extractor, terminology_normalizer, symptom_parser | query |
| 2 | medical_report | 病例理解 | medical_report | case_summarizer, risk_factor_analyzer, severity_estimator | query |
| 3 | retrieval | DRG 检索 | subgraph | direct_drg_lookup, multi_hop_expansion, fallback_subgraph | entities |
| 4 | reasoning | 医学推理 | reasoning_paths | llm_reasoner, deepseek_reasoner, sglang_reasoner | entities, subgraph |
| 5 | ranking | 路径排序 | ranked_paths | path_ranker, confidence_scorer, evidence_filter | reasoning_paths |
| 6 | treatment_plan | 治疗规划 | treatment_plan | treatment_generator, drug_candidate_lookup, warning_checker | medical_report, ranked_paths |
| 7 | explain | 解释生成 | answer | trace_summarizer, plain_language_explainer, limitation_writer | ranked_paths, medical_report, treatment_plan |

**文档结束**

---

*本文档由 MedReasonerAgent 项目组编制，严格参照传统软件工程需求分析规范。文档内容整合了用户需求说明、软件需求规格说明书、体系结构设计、接口契约、安全伦理约束和测试验收计划等 coursework 文档中的全部信息，并在此基础上对 DRG 入组功能、多 Agent 通讯机制、界面原型等关键模块进行了详细展开。*
