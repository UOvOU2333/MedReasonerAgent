"use client";

import { Bot, FlaskConical, AlertTriangle, Bug, Download, Loader2, CheckCircle2, XCircle, AlertTriangle as AlertIcon } from "lucide-react";
import { useState } from "react";
import { useTraceStore } from "../store/traceStore";
import { API_BASE } from "../lib/api";
import MarkdownMessage from "./MarkdownMessage";

type TCType = "normal" | "boundary" | "abnormal";

type ReviewCheck = {
  check: string;
  item: string;
  passed: boolean;
  detail: string;
};

type ReviewReport = {
  passed: boolean;
  passed_count: number;
  total_count: number;
  checks: ReviewCheck[];
  summary: string;
};

const tcTypeInfo: Record<
  TCType,
  { label: string; icon: typeof FlaskConical; description: string; color: string }
> = {
  normal: {
    label: "正常场景测试用例",
    icon: FlaskConical,
    description:
      "生成正常场景测试用例，覆盖不同诊断+手术组合的 DRG 入组验证，含完整病历 JSON 和预期 DRG 分组。",
    color: "#167a72",
  },
  boundary: {
    label: "边界场景测试用例",
    icon: AlertTriangle,
    description:
      "生成边界场景测试用例，覆盖合并症有无、年龄边界、多手术组合、性别差异等 DRG 分组边界条件。",
    color: "#c86f1d",
  },
  abnormal: {
    label: "异常场景测试用例",
    icon: Bug,
    description:
      "生成异常场景测试用例，覆盖 ICD 编码错误、信息缺失、逻辑冲突、格式错误等异常输入处理。",
    color: "#dc2626",
  },
};

export default function TCGenPanel() {
  // Read state from Zustand store (persists across tab switches)
  const tcgenResult = useTraceStore((state) => state.tcgenResult);
  const tcgenError = useTraceStore((state) => state.tcgenError);
  const tcgenGenerating = useTraceStore((state) => state.tcgenGenerating);
  const setTCGenResult = useTraceStore((state) => state.setTCGenResult);
  const setTCGenError = useTraceStore((state) => state.setTCGenError);
  const setTCGenGenerating = useTraceStore((state) => state.setTCGenGenerating);

  // Local state only for which card is active (ephemeral UI state)
  const [selectedTCType, setSelectedTCType] = useState<TCType | null>(null);

  const language = useTraceStore((state) => state.language);
  const isZh = language === "zh";

  async function generateTC(tcType: TCType) {
    setSelectedTCType(tcType);
    setTCGenGenerating(true);
    setTCGenError(null);
    setTCGenResult(null);

    const queryMap: Record<TCType, string> = {
      normal: isZh ? "生成正常场景测试用例" : "Generate normal scenario test cases",
      boundary: isZh ? "生成边界场景测试用例" : "Generate boundary scenario test cases",
      abnormal: isZh ? "生成异常场景测试用例" : "Generate abnormal scenario test cases",
    };

    try {
      const response = await fetch(`${API_BASE}/tcgen/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: queryMap[tcType],
          language,
          mode: "tcgen",
          tc_type: tcType,
          project_name: "MedReasonerAgent",
        }),
      });

      if (!response.ok) {
        throw new Error(`Generate failed: ${response.status}`);
      }
      const data = await response.json();
      setTCGenResult(data);
    } catch (err) {
      setTCGenError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setTCGenGenerating(false);
    }
  }

  function downloadTC() {
    if (!tcgenResult?.tc_final) return;
    const blob = new Blob([tcgenResult.tc_final], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const tcType = tcgenResult.tc_type || "normal";
    const tcTypeToFile: Record<string, string> = {
      normal: "tc_normal",
      boundary: "tc_boundary",
      abnormal: "tc_abnormal",
    };
    a.href = url;
    a.download = `MedReasonerAgent_${tcTypeToFile[tcType] || tcType}_V1.0.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const reviewPassed = tcgenResult?.review_report
    ? (tcgenResult.review_report as Record<string, unknown>).passed === true
    : false;

  return (
    <section className="tcgen-panel">
      <div className="tcgen-header">
        <Bot size={20} />
        <div>
          <strong>{isZh ? "测试用例生成智能体" : "Test Case Generation Agent"}</strong>
          <span className="tcgen-subtitle">
            {isZh
              ? "基于 DRG 分组规则和病历模板，自动生成正常、边界、异常三类测试用例"
              : "Auto-generate normal, boundary, and abnormal DRG test cases based on grouping rules and medical record templates"}
          </span>
        </div>
      </div>

      <div className="tcgen-cards">
        {(Object.keys(tcTypeInfo) as TCType[]).map((tcType) => {
          const info = tcTypeInfo[tcType];
          const Icon = info.icon;
          const isActive = selectedTCType === tcType;
          return (
            <button
              key={tcType}
              className={`tcgen-card ${isActive ? "active" : ""}`}
              onClick={() => generateTC(tcType)}
              disabled={tcgenGenerating}
              style={{ borderColor: isActive ? info.color : undefined }}
            >
              <div className="tcgen-card-icon" style={{ background: info.color }}>
                {tcgenGenerating && isActive ? <Loader2 size={28} className="spin" /> : <Icon size={28} />}
              </div>
              <strong>{info.label}</strong>
              <p>{info.description}</p>
              {tcgenGenerating && isActive ? (
                <span className="generating-label">{isZh ? "生成中..." : "Generating..."}</span>
              ) : null}
            </button>
          );
        })}
      </div>

      {tcgenError ? <div className="tcgen-error">❌ {tcgenError}</div> : null}

      {tcgenResult ? (
        <div className="tcgen-result">
          <div className="result-header">
            <span>
              {isZh ? "生成完成" : "Generation Complete"} — {tcTypeInfo[tcgenResult.tc_type as TCType]?.label ?? tcgenResult.tc_type}
              {" "}
              {reviewPassed
                ? isZh ? "✅ 审核通过" : "✅ Review Passed"
                : isZh ? "⚠️ 审核未完全通过" : "⚠️ Review Incomplete"}
            </span>
            <button className="download-btn" onClick={downloadTC} title={isZh ? "下载测试用例" : "Download test cases"}>
              <Download size={16} /> {isZh ? "下载 .md" : "Download .md"}
            </button>
          </div>

          {tcgenResult.storage_path ? (
            <div className="storage-info">
              {isZh ? "已保存至" : "Saved to"}: <code>{tcgenResult.storage_path}</code>
            </div>
          ) : null}

          {tcgenResult.review_report ? (
            <ReviewCard
              report={tcgenResult.review_report as ReviewReport}
              isZh={isZh}
            />
          ) : null}

          <div className="tc-preview">
            <h3>{isZh ? "测试用例预览" : "Test Case Preview"}</h3>
            <div className="tc-preview-content">
              <MarkdownMessage content={tcgenResult.tc_final.slice(0, 5000) + (tcgenResult.tc_final.length > 5000 ? "\n\n*(预览截断，下载完整文档)*" : "")} />
            </div>
          </div>
        </div>
      ) : null}

      <style jsx>{`
        .tcgen-panel {
          min-height: 0;
          overflow: auto;
          padding: 22px;
          display: grid;
          align-content: start;
          gap: 20px;
        }
        .tcgen-header {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding-bottom: 16px;
          border-bottom: 1px solid var(--border);
        }
        .tcgen-header strong {
          display: block;
          font-size: 18px;
          margin-bottom: 4px;
        }
        .tcgen-subtitle {
          color: var(--muted);
          font-size: 13px;
          line-height: 1.5;
        }
        .tcgen-cards {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 14px;
        }
        .tcgen-card {
          display: grid;
          gap: 10px;
          justify-items: center;
          text-align: center;
          border: 2px solid var(--border);
          border-radius: 12px;
          background: var(--panel);
          padding: 20px 14px;
          cursor: pointer;
          transition: border-color 0.2s, box-shadow 0.2s;
        }
        .tcgen-card:hover:not(:disabled) {
          box-shadow: 0 4px 16px rgba(23, 32, 42, 0.08);
          border-color: #aaa;
        }
        .tcgen-card.active {
          box-shadow: 0 4px 20px rgba(23, 32, 42, 0.1);
        }
        .tcgen-card:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }
        .tcgen-card-icon {
          width: 52px;
          height: 52px;
          display: grid;
          place-items: center;
          border-radius: 12px;
          color: #fff;
        }
        .tcgen-card strong {
          font-size: 15px;
          color: var(--text);
        }
        .tcgen-card p {
          margin: 0;
          font-size: 12px;
          line-height: 1.5;
          color: var(--muted);
        }
        .generating-label {
          font-size: 12px;
          font-weight: 600;
          color: var(--active);
        }
        .spin {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .tcgen-error {
          background: #fef2f2;
          border: 1px solid #fca5a5;
          border-radius: 8px;
          padding: 12px;
          color: #dc2626;
          font-size: 13px;
        }
        .tcgen-result {
          display: grid;
          gap: 14px;
        }
        .result-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 10px;
          font-size: 14px;
          font-weight: 600;
        }
        .download-btn {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          border: 1px solid var(--border);
          border-radius: 8px;
          background: var(--panel);
          padding: 6px 14px;
          font-size: 13px;
          cursor: pointer;
          color: var(--text);
        }
        .download-btn:hover {
          background: #eef1f5;
        }
        .storage-info {
          font-size: 13px;
          color: var(--muted);
        }
        .storage-info code {
          background: #f6f8fb;
          border: 1px solid var(--border);
          border-radius: 4px;
          padding: 2px 6px;
          font-size: 12px;
        }
        .review-card {
          border: 1px solid var(--border);
          border-radius: 10px;
          background: var(--panel);
          overflow: hidden;
        }
        .review-card-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 14px;
          border-bottom: 1px solid var(--border);
          background: #fafbfc;
        }
        .review-card-header .review-summary {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          font-weight: 700;
        }
        .review-card-header .review-badge {
          font-size: 11px;
          font-weight: 700;
          border-radius: 4px;
          padding: 2px 8px;
        }
        .review-badge.pass { background: #edf8f1; color: #1f8a4c; }
        .review-badge.fail { background: #fef2f2; color: #dc2626; }
        .review-checks {
          display: grid;
          gap: 0;
        }
        .review-check-row {
          display: grid;
          grid-template-columns: 28px 80px 1fr auto;
          align-items: center;
          gap: 8px;
          padding: 8px 14px;
          font-size: 12px;
          border-bottom: 1px solid #f0f2f5;
        }
        .review-check-row:last-child { border-bottom: 0; }
        .review-check-row.failed { background: #fffaf8; }
        .review-check-row .check-icon {
          display: grid;
          place-items: center;
        }
        .review-check-row .check-id {
          font-weight: 700;
          font-family: monospace;
          font-size: 11px;
          color: var(--muted);
        }
        .review-check-row .check-item {
          font-weight: 600;
          color: var(--text);
        }
        .review-check-row .check-detail {
          text-align: right;
          font-size: 11px;
          color: var(--muted);
          max-width: 220px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .review-check-row.failed .check-detail {
          color: #dc2626;
          font-weight: 600;
        }
        .tc-preview {
          border: 1px solid var(--border);
          border-radius: 8px;
          background: var(--panel);
          max-height: 520px;
          overflow: auto;
        }
        .tc-preview h3 {
          margin: 0;
          padding: 10px 14px;
          font-size: 13px;
          border-bottom: 1px solid var(--border);
          position: sticky;
          top: 0;
          background: var(--panel);
        }
        .tc-preview-content {
          padding: 14px;
        }
      `}</style>
    </section>
  );
}


// ── 审核报告卡片 ──

function ReviewCard({ report, isZh }: { report: ReviewReport; isZh: boolean }) {
  const sorted = [...report.checks].sort((a, b) => (a.passed === b.passed ? 0 : a.passed ? 1 : -1));
  const failCount = report.total_count - report.passed_count;

  return (
    <div className="review-card">
      <div className="review-card-header">
        <div className="review-summary">
          {report.passed ? (
            <CheckCircle2 size={18} color="#1f8a4c" />
          ) : (
            <AlertIcon size={18} color="#dc2626" />
          )}
          <span>
            {report.passed
              ? isZh ? "审核全部通过" : "All checks passed"
              : isZh
                ? `审核报告：${report.passed_count}/${report.total_count} 通过`
                : `Review: ${report.passed_count}/${report.total_count} passed`}
          </span>
        </div>
        <span className={`review-badge ${report.passed ? "pass" : "fail"}`}>
          {report.passed
            ? isZh ? "合格" : "PASS"
            : isZh
              ? `${failCount} 项未通过`
              : `${failCount} failed`}
        </span>
      </div>
      <div className="review-checks">
        {sorted.map((check) => (
          <div
            key={`${check.check}-${check.item}`}
            className={`review-check-row ${check.passed ? "" : "failed"}`}
            title={check.detail}
          >
            <div className="check-icon">
              {check.passed ? (
                <CheckCircle2 size={15} color="#1f8a4c" />
              ) : (
                <XCircle size={15} color="#dc2626" />
              )}
            </div>
            <span className="check-id">{check.check}</span>
            <span className="check-item">{check.item}</span>
            <span className="check-detail">{check.detail}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
