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
};

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
  setLanguage: (language) => set({ language }),
  startRun: (query, language) =>
    set({
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
      finalState: {},
      answer: "",
    }),
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
    set({
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
    }),
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
  };
  return labels[node] ?? node;
}

function formatUserMessage(event: TraceEvent, language: "zh" | "en") {
  const selected = event.selected_option ?? event.selected_tool;
  const title = nodeTitle(event.node ?? "");
  const output = stringifyOutput(event.output);
  const shortOutput = output.length > 260 ? `${output.slice(0, 260)}...` : output;
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
  const output = stringifyOutput(event.output);
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
  };
  return (language === "zh" ? zh : en)[node ?? ""] ?? "";
}

function stringifyOutput(output: unknown) {
  if (output === undefined || output === null) {
    return "No output.";
  }
  if (typeof output === "string") {
    return output;
  }
  return JSON.stringify(output, null, 2);
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
  const text = typeof value === "string" ? value : JSON.stringify(value);
  if (!text) {
    return "";
  }
  return text.length > 180 ? `${text.slice(0, 180)}...` : text;
}
