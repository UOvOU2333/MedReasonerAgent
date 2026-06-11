import { create } from "zustand";

export type TraceEvent = {
  event: "node_start" | "node_end" | "complete" | "error" | string;
  node?: string;
  decision_id?: string;
  parent_decision_id?: string | null;
  timestamp?: number;
  output?: unknown;
  available_tools?: string[];
  selected_tool?: string;
  decision_options?: string[];
  selected_option?: string;
  state?: Record<string, unknown>;
  answer?: string;
  trace?: Array<Record<string, unknown>>;
};

export type ChatMessage = {
  id: string;
  role: "user" | "agent" | "system";
  title: string;
  content: string;
  details?: string;
  node?: string;
};

type TestMeta = {
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  error: number;
  xfailed: number;
  xpassed: number;
  pass_rate: number;
  report_date: string;
};

type DocGenResult = {
  answer: string;
  doc_final: string;
  doc_type: string;
  storage_path: string;
  pdf_url?: string;
  pdf_path?: string;
  review_report: Record<string, unknown>;
  test_meta?: TestMeta;
} | null;

type TCGenResult = {
  answer: string;
  tc_final: string;
  tc_type: string;
  storage_path: string;
  pdf_url?: string;
  pdf_path?: string;
  review_report: Record<string, unknown>;
} | null;

type DocGenState = {
  docgenResult: DocGenResult;
  docgenError: string | null;
  docgenGenerating: boolean;
  docgenCompletedSteps: number;
  setDocGenResult: (r: DocGenResult) => void;
  setDocGenError: (e: string | null) => void;
  setDocGenGenerating: (g: boolean) => void;
  setDocGenCompletedSteps: (s: number) => void;
};

type TCGenState = {
  tcgenResult: TCGenResult;
  tcgenError: string | null;
  tcgenGenerating: boolean;
  setTCGenResult: (r: TCGenResult) => void;
  setTCGenError: (e: string | null) => void;
  setTCGenGenerating: (g: boolean) => void;
};

type PanelState = DocGenState & TCGenState;

type TraceState = {
  events: TraceEvent[];
  messages: ChatMessage[];
  language: "zh" | "en";
  activeNode: string | null;
  decisionSequence: string[];
  completedNodes: string[];
  selectedTools: Record<string, string>;
  availableTools: Record<string, string[]>;
  decisionParents: Record<string, string | null>;
  finalState: Record<string, unknown>;
  answer: string;
  setLanguage: (language: "zh" | "en") => void;
  startRun: (query: string, language: "zh" | "en") => void;
  addEvent: (event: TraceEvent) => void;
  reset: () => void;
} & PanelState;

export const useTraceStore = create<TraceState>((set) => ({
  events: [],
  messages: [],
  language: "zh",
  activeNode: null,
  decisionSequence: [],
  completedNodes: [],
  selectedTools: {},
  availableTools: {},
  decisionParents: {},
  finalState: {},
  answer: "",

  // Panel state — preserved across tab switches
  docgenResult: null,
  docgenError: null,
  docgenGenerating: false,
  docgenCompletedSteps: 0,
  tcgenResult: null,
  tcgenError: null,
  tcgenGenerating: false,

  setLanguage: (language) => set({ language }),
  startRun: (query, language) =>
    set((state) => ({
      events: [],
      language,
      messages: [
        {
          id: `user-${Date.now()}`,
          role: "user",
          title: language === "zh" ? "用户" : "User",
          content: query,
        },
      ],
      activeNode: null,
      decisionSequence: [],
      completedNodes: [],
      selectedTools: {},
      availableTools: {},
      decisionParents: {},
      finalState: {},
      answer: "",
      // Preserve panel results on new DRG run
      docgenResult: state.docgenResult,
      docgenError: state.docgenError,
      docgenGenerating: false,
      docgenCompletedSteps: state.docgenCompletedSteps,
      tcgenResult: state.tcgenResult,
      tcgenError: state.tcgenError,
      tcgenGenerating: false,
    })),
  addEvent: (event) =>
    set((state) => {
      const completed = new Set(state.completedNodes);
      const availableTools = { ...state.availableTools };
      const selectedTools = { ...state.selectedTools };
      const decisionParents = { ...state.decisionParents };
      const decisionSequence = [...state.decisionSequence];
      const messages = [...state.messages];
      const decisionId = event.decision_id ?? event.node;

      if (event.event === "node_start" && decisionId && !decisionSequence.includes(decisionId)) {
        decisionSequence.push(decisionId);
      }
      if (decisionId && (event.available_tools || event.decision_options)) {
        availableTools[decisionId] = event.decision_options ?? event.available_tools ?? [];
      }
      if (decisionId && event.parent_decision_id !== undefined) {
        decisionParents[decisionId] = event.parent_decision_id;
      }
      if (event.event === "node_end" && event.node) {
        completed.add(event.node);
        if (event.selected_tool || event.selected_option) {
          selectedTools[event.node] = event.selected_option ?? event.selected_tool ?? "";
        }
        messages.push({
          id: `${event.node}-${event.timestamp ?? Date.now()}`,
          role: "agent",
          title: nodeTitle(event.node),
          node: event.node,
          content: formatUserMessage(event, state.language),
          details: formatInternalDetails(event, state.language),
        });
      }
      if (event.event === "complete" && event.answer) {
        messages.push({
          id: `answer-${event.timestamp ?? Date.now()}`,
          role: "system",
          title: state.language === "zh" ? "最终回复" : "Final Answer",
          content: event.answer,
        });
      }
      return {
        events: [...state.events, event],
        messages,
        activeNode: event.event === "complete" ? null : event.event === "node_start" ? event.node ?? null : state.activeNode,
        decisionSequence,
        completedNodes: Array.from(completed),
        selectedTools,
        availableTools,
        decisionParents,
        finalState: event.state ?? state.finalState,
        answer: event.answer ?? state.answer,
      };
    }),
  reset: () =>
    set((state) => ({
      events: [],
      messages: [],
      activeNode: null,
      decisionSequence: [],
      completedNodes: [],
      selectedTools: {},
      availableTools: {},
      decisionParents: {},
      finalState: {},
      answer: "",
      // Preserve panel results — only clear running states
      docgenGenerating: false,
      docgenError: null,
      tcgenGenerating: false,
      tcgenError: null,
      docgenResult: state.docgenResult,
      docgenCompletedSteps: state.docgenCompletedSteps,
      tcgenResult: state.tcgenResult,
    })),
  // Panel setters
  setDocGenResult: (r) => set({ docgenResult: r }),
  setDocGenError: (e) => set({ docgenError: e }),
  setDocGenGenerating: (g) => set({ docgenGenerating: g }),
  setDocGenCompletedSteps: (s) => set({ docgenCompletedSteps: s }),
  setTCGenResult: (r) => set({ tcgenResult: r }),
  setTCGenError: (e) => set({ tcgenError: e }),
  setTCGenGenerating: (g) => set({ tcgenGenerating: g }),
}));

function nodeTitle(node: string) {
  const labels: Record<string, string> = {
    supervisor: "Supervisor Agent",
    entity: "Entity Agent",
    medical_report: "Medical Report Agent",
    retrieval: "Retrieval Agent",
    reasoning: "Reasoning Agent",
    ranking: "Ranking Agent",
    treatment_plan: "Treatment Plan Agent",
    explain: "Explain Agent",
    doc_supervisor: "Doc Supervisor Agent",
    code_scanner: "Code Scanner Agent",
    context_collector: "Context Collector Agent",
    doc_composer: "Doc Composer Agent",
    doc_formatter: "Doc Formatter Agent",
    doc_reviewer: "Doc Reviewer Agent",
    doc_receiver: "Doc Receiver Agent",
    doc_validator: "Doc Validator Agent",
    doc_metadata_tagger: "Metadata Tagger Agent",
    doc_storer: "Doc Storer Agent",
    doc_notifier: "Doc Notifier Agent",
  };
  return labels[node] ?? node;
}

function formatUserMessage(event: TraceEvent, language: "zh" | "en") {
  const selected = event.selected_option ?? event.selected_tool;
  const title = nodeTitle(event.node ?? "");
  const shortOutput = summarizeOutput(event.output, event.node, language);
  if (language === "en") {
    return [
      `**${title}** completed this step${selected ? ` using **${selected}**` : ""}.`,
      userFriendlyAction(event.node, language),
      "",
      `**Result summary:** ${shortOutput}`,
    ].join("\n");
  }
  return [
    `**${title}** 已完成本步骤${selected ? `，使用了 **${selected}**` : ""}。`,
    userFriendlyAction(event.node, language),
    "",
    `**结果摘要：** ${shortOutput}`,
  ].join("\n");
}

function formatInternalDetails(event: TraceEvent, language: "zh" | "en") {
  const selected = event.selected_tool ? `Selected tool: ${event.selected_tool}\n\n` : "";
  const output = formatFullOutput(event.output);
  const context = summarizeState(event.state);
  const label = language === "zh" ? "Agent 间传递的上下文" : "Context passed between agents";
  return `${selected}${output}${context ? `\n\n${label}:\n${context}` : ""}`;
}

function userFriendlyAction(node: string | undefined, language: "zh" | "en") {
  const zh: Record<string, string> = {
    supervisor: "系统判断了你的问题适合走哪种医学推理流程。",
    entity: "系统从你的描述中提取了关键医学概念。",
    medical_report: "系统把你的描述整理成病例理解摘要。",
    retrieval: "系统根据关键概念检索了 DRG 知识图谱上下文。",
    reasoning: "系统基于病例和图谱线索生成了医学推理路径。",
    ranking: "系统对候选推理路径做了排序。",
    treatment_plan: "系统生成了带限制说明的治疗方案草案。",
    explain: "系统把前面步骤整合成用户可读的解释。",
    doc_supervisor: "文档生成器判定了你需要的文档类型。",
    code_scanner: "系统扫描了项目代码结构，提取了文件树和模块清单。",
    context_collector: "系统收集了项目背景信息（README、架构说明、需求文档等）。",
    doc_composer: "系统根据代码分析和上下文，按照规范模板生成文档初稿。",
    doc_formatter: "系统对文档进行了格式化处理，确保表格对齐和章节规范。",
    doc_reviewer: "系统审核了文档的完整性、格式规范和编号连续性。",
    doc_receiver: "虚拟文档系统接收了待存储的文档。",
    doc_validator: "系统验证了文档的基本格式规范。",
    doc_metadata_tagger: "系统为文档添加了版本、日期等元数据标签。",
    doc_storer: "系统将文档保存到了文件系统中。",
    doc_notifier: "系统完成了文档存储的通知和索引更新。",
  };
  const en: Record<string, string> = {
    supervisor: "The system decided which medical reasoning workflow fits your question.",
    entity: "The system extracted key medical concepts from your description.",
    medical_report: "The system organized your description into a case-understanding summary.",
    retrieval: "The system retrieved DRG graph context from the extracted concepts.",
    reasoning: "The system generated medical reasoning paths from the case and graph context.",
    ranking: "The system ranked the candidate reasoning paths.",
    treatment_plan: "The system generated a treatment-plan draft with limitations.",
    explain: "The system merged prior steps into a user-readable explanation.",
    doc_supervisor: "The document generator determined your requested document type.",
    code_scanner: "The system scanned project code structure, extracting file tree and module list.",
    context_collector: "The system collected project context (README, architecture, requirements).",
    doc_composer: "The system composed a document draft based on code analysis and templates.",
    doc_formatter: "The system formatted the document, aligning tables and normalizing sections.",
    doc_reviewer: "The system reviewed the document for completeness and format compliance.",
    doc_receiver: "The virtual document system received the document for storage.",
    doc_validator: "The system validated basic document format requirements.",
    doc_metadata_tagger: "The system tagged the document with version and date metadata.",
    doc_storer: "The system saved the document to the filesystem.",
    doc_notifier: "The system updated the document index and sent notifications.",
  };
  return (language === "zh" ? zh : en)[node ?? ""] ?? "";
}

function stringifyOutput(output: unknown) {
  if (output === undefined || output === null) {
    return "No output.";
  }
  if (typeof output === "string") {
    return normalizeEscapedText(output);
  }
  return JSON.stringify(output, null, 2);
}

function summarizeOutput(output: unknown, node: string | undefined, language: "zh" | "en") {
  if (output === undefined || output === null) {
    return language === "zh" ? "无输出。" : "No output.";
  }
  if (node === "treatment_plan" && isRecord(output)) {
    const parts: string[] = [];
    const options = asStringList(output.options);
    const warnings = asStringList(output.warnings);
    if (output.drg_code) parts.push(`DRG: ${String(output.drg_code)}`);
    if (options.length) parts.push(`${language === "zh" ? "方案" : "Options"}: ${options.slice(0, 2).join("；")}`);
    if (output.confidence) parts.push(`${language === "zh" ? "置信度" : "Confidence"}: ${String(output.confidence)}`);
    if (warnings.length) parts.push(`${language === "zh" ? "提示" : "Warnings"}: ${warnings.slice(0, 1).join("；")}`);
    if (parts.length) return clipText(parts.join("\n"));
  }
  if (isRecord(output)) {
    const preferred = ["drg", "mdc", "adrg", "confidence", "summary", "warning", "text"];
    const lines = preferred
      .filter((key) => output[key] !== undefined)
      .map((key) => `${key}: ${compactValue(output[key])}`);
    return clipText(lines.length ? lines.join("\n") : JSON.stringify(output, null, 2));
  }
  return clipText(stringifyOutput(output));
}

function formatFullOutput(output: unknown) {
  if (isRecord(output) || Array.isArray(output)) {
    return `\`\`\`json\n${JSON.stringify(output, null, 2)}\n\`\`\``;
  }
  return stringifyOutput(output);
}

function normalizeEscapedText(text: string) {
  return text.replace(/\\n/g, "\n").replace(/\\t/g, "\t").replace(/\\"/g, '"');
}

function clipText(text: string, max = 320) {
  const normalized = normalizeEscapedText(text).trim();
  return normalized.length > max ? `${normalized.slice(0, max)}...` : normalized;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asStringList(value: unknown) {
  if (!Array.isArray(value)) return [];
  return value.map((item) => (typeof item === "string" ? item : JSON.stringify(item))).filter(Boolean);
}

function summarizeState(state?: Record<string, unknown>) {
  if (!state) {
    return "";
  }
  const keys = ["entities", "subgraph", "reasoning_paths", "ranked_paths", "medical_report", "treatment_plan"];
  return keys
    .filter((key) => state[key] !== undefined)
    .map((key) => `${key}: ${compactValue(state[key])}`)
    .join("\n");
}

function compactValue(value: unknown) {
  const text = typeof value === "string" ? normalizeEscapedText(value) : JSON.stringify(value);
  if (!text) {
    return "";
  }
  return text.length > 180 ? `${text.slice(0, 180)}...` : text;
}
