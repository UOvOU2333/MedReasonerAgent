import { create } from "zustand";

export type TraceEvent = {
  event: "node_start" | "node_end" | "complete" | "error" | string;
  node?: string;
  timestamp?: number;
  output?: unknown;
  state?: Record<string, unknown>;
  answer?: string;
  trace?: Array<Record<string, unknown>>;
};

type TraceState = {
  events: TraceEvent[];
  activeNode: string | null;
  completedNodes: string[];
  finalState: Record<string, unknown>;
  answer: string;
  addEvent: (event: TraceEvent) => void;
  reset: () => void;
};

export const useTraceStore = create<TraceState>((set) => ({
  events: [],
  activeNode: null,
  completedNodes: [],
  finalState: {},
  answer: "",
  addEvent: (event) =>
    set((state) => {
      const completed = new Set(state.completedNodes);
      if (event.event === "node_end" && event.node) {
        completed.add(event.node);
      }
      return {
        events: [...state.events, event],
        activeNode: event.event === "node_start" ? event.node ?? null : state.activeNode,
        completedNodes: Array.from(completed),
        finalState: event.state ?? state.finalState,
        answer: event.answer ?? state.answer,
      };
    }),
  reset: () =>
    set({
      events: [],
      activeNode: null,
      completedNodes: [],
      finalState: {},
      answer: "",
    }),
}));
