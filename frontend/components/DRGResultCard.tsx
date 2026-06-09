"use client";

import { Activity, AlertTriangle } from "lucide-react";
import { useTraceStore } from "../store/traceStore";

export default function DRGResultCard() {
  const drgResult = useTraceStore((state) => state.finalState.drg_result) as
    | {
        drg?: string;
        drg_name?: string;
        mdc?: string;
        mdc_name?: string;
        adrg?: string;
        adrg_name?: string;
        complication?: string;
        confidence?: number;
        confidence_level?: string;
        reasoning_steps?: string[];
        warning?: string;
      }
    | undefined;

  if (!drgResult?.drg || drgResult.drg === "N/A") {
    return null;
  }

  const conf = drgResult.confidence ?? 0;
  const barLen = 10;
  const filled = Math.round(conf * barLen);
  const bar = "█".repeat(filled) + "░".repeat(barLen - filled);

  const compLabel: Record<string, string> = {
    MCC: "严重合并症 (MCC)",
    CC: "一般合并症 (CC)",
    none: "无合并症",
  };

  const confColor =
    conf >= 0.9 ? "#1f8a4c" : conf >= 0.7 ? "#c86f1d" : "#dc2626";

  return (
    <section className="panel drg-result">
      <h2>
        <Activity size={16} /> DRG 入组结果
      </h2>

      <div className="drg-hero">
        <span className="drg-code">{drgResult.drg}</span>
        <span className="drg-name">{drgResult.drg_name || ""}</span>
      </div>

      <table className="drg-table">
        <tbody>
          <tr>
            <td>MDC</td>
            <td>
              {drgResult.mdc}（{drgResult.mdc_name}）
            </td>
          </tr>
          <tr>
            <td>ADRG</td>
            <td>
              {drgResult.adrg}（{drgResult.adrg_name}）
            </td>
          </tr>
          <tr>
            <td>并发症等级</td>
            <td>{compLabel[drgResult.complication ?? "none"] ?? drgResult.complication}</td>
          </tr>
          <tr>
            <td>置信度</td>
            <td>
              <span style={{ color: confColor, fontWeight: 700 }}>
                {drgResult.confidence_level ?? ""} {conf}
              </span>
              <span className="conf-bar">{bar}</span>
            </td>
          </tr>
        </tbody>
      </table>

      {drgResult.reasoning_steps && drgResult.reasoning_steps.length > 0 ? (
        <details className="drg-steps">
          <summary>入组路径详情</summary>
          <ol>
            {drgResult.reasoning_steps.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </details>
      ) : null}

      {drgResult.warning ? (
        <div className="drg-warning">
          <AlertTriangle size={14} />
          <span>{drgResult.warning}</span>
        </div>
      ) : null}

      <style jsx>{`
        h2 {
          display: flex;
          align-items: center;
          gap: 8px;
          margin: 0 0 12px;
          font-size: 15px;
        }
        .drg-hero {
          display: flex;
          align-items: baseline;
          gap: 14px;
          margin-bottom: 14px;
          padding: 12px 14px;
          background: #f0f8f4;
          border-radius: 8px;
          border-left: 4px solid #1f8a4c;
        }
        .drg-code {
          font-size: 28px;
          font-weight: 800;
          font-family: monospace;
          color: #1f8a4c;
        }
        .drg-name {
          font-size: 14px;
          font-weight: 600;
          color: var(--text);
        }
        .drg-table {
          width: 100%;
          border-collapse: collapse;
          margin-bottom: 10px;
          font-size: 13px;
        }
        .drg-table td {
          padding: 6px 10px;
          border-bottom: 1px solid #eef1f5;
        }
        .drg-table td:first-child {
          font-weight: 600;
          color: var(--muted);
          width: 90px;
        }
        .conf-bar {
          display: block;
          font-family: monospace;
          font-size: 11px;
          color: var(--muted);
          margin-top: 2px;
        }
        .drg-steps {
          margin-bottom: 10px;
          font-size: 12px;
          color: var(--muted);
        }
        .drg-steps summary {
          cursor: pointer;
          font-weight: 600;
          margin-bottom: 6px;
        }
        .drg-steps ol {
          margin: 0;
          padding-left: 18px;
        }
        .drg-steps li {
          margin-bottom: 4px;
          line-height: 1.5;
        }
        .drg-warning {
          display: flex;
          align-items: flex-start;
          gap: 6px;
          border-left: 3px solid #c86f1d;
          padding: 8px 10px;
          color: #6c3d10;
          font-size: 11px;
          line-height: 1.4;
          background: #fefaf4;
          border-radius: 0 6px 6px 0;
        }
      `}</style>
    </section>
  );
}
