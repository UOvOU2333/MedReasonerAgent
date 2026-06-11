"use client";

import { ShieldAlert } from "lucide-react";
import { useTraceStore } from "../store/traceStore";

export default function TreatmentCard() {
  const plan = useTraceStore((state) => state.finalState.treatment_plan as TreatmentPlan | undefined);
  const options = Array.isArray(plan?.options) ? plan.options : [];
  const warnings = Array.isArray(plan?.warnings) ? plan.warnings : [];

  return (
    <section className="panel treatment">
      <h2>
        <ShieldAlert size={16} /> Treatment Plan
      </h2>
      {plan ? (
        <div className="plan-body">
          {plan.drg_code ? <div className="meta">DRG: {plan.drg_code}</div> : null}
          {options.length ? (
            <ul>
              {options.map((item, index) => <li key={index}>{String(item)}</li>)}
            </ul>
          ) : (
            <pre>{plan.text || "No structured treatment options returned."}</pre>
          )}
          {plan.mechanism ? <p>{plan.mechanism}</p> : null}
          {plan.confidence ? <div className="meta">Confidence: {plan.confidence}</div> : null}
        </div>
      ) : (
        <pre>Waiting for treatment plan agent.</pre>
      )}
      {warnings.length ? (
        <div className="warning">{warnings.map(String).join("；")}</div>
      ) : null}
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
        .plan-body {
          display: grid;
          gap: 8px;
          margin-bottom: 10px;
          font-size: 12px;
          line-height: 1.5;
        }
        ul {
          margin: 0;
          padding-left: 18px;
        }
        p {
          margin: 0;
        }
        .meta {
          color: var(--muted);
          font-weight: 700;
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

type TreatmentPlan = {
  text?: string;
  warning?: string;
  drg_code?: string;
  options?: unknown[];
  warnings?: unknown[];
  mechanism?: string;
  confidence?: string;
};
