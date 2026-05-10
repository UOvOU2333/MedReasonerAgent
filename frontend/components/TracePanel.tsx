"use client";

import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import { useTraceStore } from "../store/traceStore";

const labels: Record<string, string> = {
  entity: "Entity",
  medical_report: "Medical Report",
  retrieval: "Retrieval",
  reasoning: "Reasoning",
  ranking: "Ranking",
  treatment_plan: "Treatment",
  explain: "Explain",
};

export default function TracePanel() {
  const events = useTraceStore((state) => state.events);
  const activeNode = useTraceStore((state) => state.activeNode);
  const completed = useTraceStore((state) => state.completedNodes);

  const nodes = ["entity", "medical_report", "retrieval", "reasoning", "ranking", "treatment_plan", "explain"];

  return (
    <section className="panel trace-panel">
      <h2>Execution Trace</h2>
      <div className="trace-steps">
        {nodes.map((node) => {
          const done = completed.includes(node);
          const active = activeNode === node && !done;
          return (
            <div className="trace-step" key={node}>
              {done ? <CheckCircle2 size={16} /> : active ? <Loader2 size={16} className="spin" /> : <Circle size={16} />}
              <span>{labels[node]}</span>
              <strong>{done ? "OK" : active ? "RUNNING" : "WAIT"}</strong>
            </div>
          );
        })}
      </div>
      <div className="event-log">
        {events.slice(-8).map((event, index) => (
          <div key={`${event.timestamp}-${index}`}>
            <span>{event.event}</span>
            <b>{event.node}</b>
          </div>
        ))}
      </div>
      <style jsx>{`
        .trace-steps {
          display: grid;
          gap: 8px;
        }
        .trace-step {
          display: grid;
          grid-template-columns: 18px 1fr auto;
          align-items: center;
          gap: 8px;
          font-size: 13px;
        }
        .trace-step strong {
          font-size: 11px;
          color: var(--muted);
        }
        .event-log {
          margin-top: 12px;
          border-top: 1px solid var(--border);
          padding-top: 10px;
          display: grid;
          gap: 6px;
          font-size: 12px;
          color: var(--muted);
        }
        .event-log div {
          display: flex;
          justify-content: space-between;
          gap: 8px;
        }
        .spin {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </section>
  );
}
