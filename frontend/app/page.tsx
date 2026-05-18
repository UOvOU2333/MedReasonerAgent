"use client";

import { FormEvent, useRef, useState } from "react";
import AgentGraph from "../components/AgentGraph";
import ConversationPanel from "../components/ConversationPanel";
import { streamReasoning } from "../lib/websocket";
import { useTraceStore } from "../store/traceStore";

export default function Home() {
  const [query, setQuery] = useState("Patient has chest pain, fever, diabetes risk, and abnormal inflammatory markers.");
  const [running, setRunning] = useState(false);
  const language = useTraceStore((state) => state.language);
  const addEvent = useTraceStore((state) => state.addEvent);
  const setLanguage = useTraceStore((state) => state.setLanguage);
  const startRun = useTraceStore((state) => state.startRun);
  const stopRef = useRef<null | (() => void)>(null);

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) {
      return;
    }
    stopRef.current?.();
    startRun(query, language);
    setRunning(true);
    stopRef.current = streamReasoning(
      query,
      language,
      (traceEvent) => {
        addEvent(traceEvent);
        if (traceEvent.event === "complete" || traceEvent.event === "error") {
          setRunning(false);
        }
      },
      () => setRunning(false),
    );
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">MedReasonerAgent</div>
        <div className="run-status">{running ? (language === "zh" ? "多 Agent 推理中" : "Running multi-agent reasoning") : language === "zh" ? "就绪" : "Ready"}</div>
      </header>
      <section className="workspace">
        <ConversationPanel
          query={query}
          running={running}
          language={language}
          onQueryChange={setQuery}
          onLanguageChange={setLanguage}
          onSubmit={submit}
        />
        <AgentGraph />
      </section>
    </main>
  );
}
