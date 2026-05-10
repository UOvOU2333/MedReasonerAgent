"use client";

import { FileText } from "lucide-react";
import { useTraceStore } from "../store/traceStore";

export default function ReportCard() {
  const report = useTraceStore((state) => state.finalState.medical_report as { text?: string; warning?: string } | undefined);

  return (
    <section className="panel">
      <h2>
        <FileText size={16} /> Medical Report
      </h2>
      <pre>{report?.text || "Waiting for medical report agent."}</pre>
      {report?.warning ? <p className="muted">{report.warning}</p> : null}
      <style jsx>{`
        h2 {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        pre {
          white-space: pre-wrap;
          word-break: break-word;
          margin: 0;
          font-size: 12px;
          line-height: 1.5;
        }
      `}</style>
    </section>
  );
}
