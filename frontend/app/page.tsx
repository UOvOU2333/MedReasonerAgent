"use client";

import { FormEvent, useRef, useState } from "react";
import AgentGraph from "../components/AgentGraph";
import ConversationPanel from "../components/ConversationPanel";
import DocGenPanel from "../components/DocGenPanel";
import VDocPanel from "../components/VDocPanel";
import { streamReasoning } from "../lib/websocket";
import { useTraceStore } from "../store/traceStore";

type Tab = "drg" | "docgen" | "vdoc";

const tabs: { key: Tab; label: { zh: string; en: string } }[] = [
  { key: "drg", label: { zh: "DRG 入组", en: "DRG Grouping" } },
  { key: "docgen", label: { zh: "文档生成", en: "Doc Generator" } },
  { key: "vdoc", label: { zh: "虚拟文档", en: "Virtual Docs" } },
];

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("drg");
  const [query, setQuery] = useState("Patient has chest pain, fever, diabetes risk, and abnormal inflammatory markers.");
  const [running, setRunning] = useState(false);
  const language = useTraceStore((state) => state.language);
  const addEvent = useTraceStore((state) => state.addEvent);
  const setLanguage = useTraceStore((state) => state.setLanguage);
  const startRun = useTraceStore((state) => state.startRun);
  const reset = useTraceStore((state) => state.reset);
  const stopRef = useRef<null | (() => void)>(null);

  function switchTab(tab: Tab) {
    if (running) return; // 运行中不允许切换
    stopRef.current?.();
    setActiveTab(tab);
    reset();
    setRunning(false);
  }

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
        <nav className="tab-nav">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              className={`tab-btn ${activeTab === tab.key ? "active" : ""}`}
              onClick={() => switchTab(tab.key)}
              disabled={running}
            >
              {language === "zh" ? tab.label.zh : tab.label.en}
            </button>
          ))}
        </nav>
        <div className="run-status">
          {activeTab === "drg"
            ? running
              ? language === "zh"
                ? "多 Agent 推理中"
                : "Running multi-agent reasoning"
              : language === "zh"
                ? "就绪"
                : "Ready"
            : activeTab === "docgen"
              ? language === "zh"
                ? "文档生成"
                : "Document Generation"
              : language === "zh"
                ? "文档存储系统"
                : "Document Storage System"}
        </div>
      </header>
      <section className="workspace">
        {activeTab === "drg" ? (
          <>
            <ConversationPanel
              query={query}
              running={running}
              language={language}
              onQueryChange={setQuery}
              onLanguageChange={setLanguage}
              onSubmit={submit}
            />
            <AgentGraph />
          </>
        ) : activeTab === "docgen" ? (
          <DocGenPanel />
        ) : (
          <VDocPanel />
        )}
      </section>
      <style jsx>{`
        .tab-nav {
          display: flex;
          gap: 4px;
          background: var(--bg);
          border-radius: 8px;
          padding: 3px;
        }
        .tab-btn {
          border: 0;
          background: transparent;
          padding: 6px 16px;
          border-radius: 6px;
          font-size: 13px;
          font-weight: 600;
          color: var(--muted);
          cursor: pointer;
          transition: background 0.15s, color 0.15s;
          white-space: nowrap;
        }
        .tab-btn:hover:not(:disabled) {
          background: #eef1f5;
          color: var(--text);
        }
        .tab-btn.active {
          background: var(--panel);
          color: var(--text);
          box-shadow: 0 1px 3px rgba(23, 32, 42, 0.08);
        }
        .tab-btn:disabled {
          cursor: not-allowed;
          opacity: 0.6;
        }
      `}</style>
    </main>
  );
}
