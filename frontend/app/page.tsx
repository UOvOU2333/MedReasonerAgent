"use client";

import { FormEvent, useRef, useState } from "react";
import { Play } from "lucide-react";
import AgentGraph from "../components/AgentGraph";
import ReportCard from "../components/ReportCard";
import TracePanel from "../components/TracePanel";
import TreatmentCard from "../components/TreatmentCard";
import { streamReasoning } from "../lib/websocket";
import { useTraceStore } from "../store/traceStore";

export default function Home() {
  const [query, setQuery] = useState("Patient has chest pain, fever, diabetes risk, and abnormal inflammatory markers.");
  const [running, setRunning] = useState(false);
  const addEvent = useTraceStore((state) => state.addEvent);
  const reset = useTraceStore((state) => state.reset);
  const stopRef = useRef<null | (() => void)>(null);

  function submit(event: FormEvent) {
    event.preventDefault();
    stopRef.current?.();
    reset();
    setRunning(true);
    stopRef.current = streamReasoning(
      query,
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
        <form className="query-form" onSubmit={submit}>
          <input value={query} onChange={(event) => setQuery(event.target.value)} />
          <button type="submit" disabled={running}>
            <Play size={16} /> {running ? "Running" : "Run"}
          </button>
        </form>
      </header>
      <section className="workspace">
        <div className="graph-pane">
          <AgentGraph />
        </div>
        <aside className="side-pane">
          <TracePanel />
          <ReportCard />
          <TreatmentCard />
        </aside>
      </section>
      <style jsx>{`
        button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
        }
        button:disabled {
          opacity: 0.68;
          cursor: wait;
        }
      `}</style>
    </main>
  );
}
