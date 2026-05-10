"use client";

import { ShieldAlert } from "lucide-react";
import { useTraceStore } from "../store/traceStore";

export default function TreatmentCard() {
  const plan = useTraceStore((state) => state.finalState.treatment_plan as { text?: string; warning?: string } | undefined);

  return (
    <section className="panel treatment">
      <h2>
        <ShieldAlert size={16} /> Treatment Plan
      </h2>
      <pre>{plan?.text || "Waiting for treatment plan agent."}</pre>
      <div className="warning">{plan?.warning || "Outputs are clinical decision support, not a diagnosis or prescription."}</div>
      <style jsx>{`
        h2 {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        pre {
          white-space: pre-wrap;
          word-break: break-word;
          margin: 0 0 10px;
          font-size: 12px;
          line-height: 1.5;
        }
        .warning {
          border-left: 3px solid #c86f1d;
          padding-left: 10px;
          color: #6c3d10;
          font-size: 12px;
        }
      `}</style>
    </section>
  );
}
