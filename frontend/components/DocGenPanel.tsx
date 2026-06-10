"use client";

import {
  Bot, FileText, FileCode, ClipboardCheck, Loader2,
  CheckCircle2, XCircle, AlertTriangle,
} from "lucide-react";
import { useState } from "react";
import { useTraceStore } from "../store/traceStore";
import { API_BASE } from "../lib/api";
import MarkdownMessage from "./MarkdownMessage";

type DocType = "requirements" | "architecture" | "testing";

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

type Step = {
  label: string;
  sub: string;
};

const docTypeInfo: Record<
  DocType,
  { label: string; icon: typeof FileText; description: string; color: string }
> = {
  requirements: {
    label: "需求分析文档",
    icon: FileText,
    description:
      "生成完整的需求分析文档，含系统功能需求、用例分析、用户故事、非功能需求、数据需求、接口需求和约束假设。",
    color: "#167a72",
  },
  architecture: {
    label: "架构设计文档",
    icon: FileCode,
    description:
      "生成完整的架构设计文档，含总体架构图、模块划分、数据流设计、组件通信、技术选型和部署架构。",
    color: "#5b4e9c",
  },
  testing: {
    label: "测试文档",
    icon: ClipboardCheck,
    description:
      "生成完整的测试文档，含测试策略、方案、实时执行数据及 LLM 分析报告。",
    color: "#c86f1d",
  },
};

const testingSteps: Step[] = [
  { label: "生成测试方案", sub: "AI 分析项目，生成测试策略与方案" },
  { label: "运行 pytest", sub: "执行全部测试用例，收集实时结果" },
  { label: "生成分析报告", sub: "LLM 基于执行数据生成结构化报告" },
];

export default function DocGenPanel() {
  // Read state from Zustand store (persists across tab switches)
  const docgenResult = useTraceStore((state) => state.docgenResult);
  const docgenError = useTraceStore((state) => state.docgenError);
  const docgenGenerating = useTraceStore((state) => state.docgenGenerating);
  const docgenCompletedSteps = useTraceStore((state) => state.docgenCompletedSteps);
  const setDocGenResult = useTraceStore((state) => state.setDocGenResult);
  const setDocGenError = useTraceStore((state) => state.setDocGenError);
  const setDocGenGenerating = useTraceStore((state) => state.setDocGenGenerating);
  const setDocGenCompletedSteps = useTraceStore((state) => state.setDocGenCompletedSteps);

  // Local state only for UI that truly needs ephemeral state
  const [selectedDocType, setSelectedDocType] = useState<DocType | null>(null);

  const language = useTraceStore((state) => state.language);
  const isZh = language === "zh";

  async function generateDoc(docType: DocType) {
    setSelectedDocType(docType);
    setDocGenGenerating(true);
    setDocGenError(null);
    setDocGenResult(null);
    setDocGenCompletedSteps(0);

    const isTesting = docType === "testing";
    const endpoint = isTesting ? `${API_BASE}/testing/generate-doc` : `${API_BASE}/docgen/generate`;

    let body: Record<string, unknown>;
    if (isTesting) {
      body = { language };
    } else {
      const queryMap: Record<string, string> = {
        requirements: isZh ? "生成需求分析文档" : "Generate requirements analysis document",
        architecture: isZh ? "生成架构设计文档" : "Generate architecture design document",
      };
      body = {
        query: queryMap[docType],
        language,
        mode: "docgen",
        doc_type: docType,
        project_name: "MedReasonerAgent",
      };
    }

    try {
      if (isTesting) {
        setDocGenCompletedSteps(1);
        const r1 = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (!r1.ok) throw new Error(`${r1.status}: ${await r1.text()}`);
        const d1 = await r1.json();
        setDocGenCompletedSteps(2);
        setDocGenResult(d1);
        setDocGenCompletedSteps(3);
      } else {
        const response = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (!response.ok) throw new Error(`Generate failed: ${response.status}`);
        const data = await response.json();
        setDocGenResult(data);
        setDocGenCompletedSteps(3);
      }
    } catch (err) {
      setDocGenError(err instanceof Error ? err.message : "Unknown error");
      setDocGenCompletedSteps(0);
    } finally {
      setDocGenGenerating(false);
    }
  }

  const reviewPassed = docgenResult?.review_report
    ? (docgenResult.review_report as Record<string, unknown>).passed === true
    : false;

  const tm = docgenResult?.test_meta;
  const passRate = tm?.pass_rate ?? 0;
  const rateColor = passRate >= 80 ? "#1f8a4c" : passRate >= 50 ? "#c86f1d" : "#dc2626";

  return (
    <section className="docgen-panel">
      <div className="docgen-header">
        <Bot size={20} />
        <div>
          <strong>{isZh ? "文档自动生成智能体" : "Document Generation Agent"}</strong>
          <span className="docgen-subtitle">
            {isZh
              ? "选择文档类型，智能体将自动分析项目并生成符合规范的文档"
              : "Select document type to auto-generate specification-compliant documentation"}
          </span>
        </div>
      </div>

      {/* ── 文档生成卡片 ── */}
      <div className="docgen-cards">
        {(Object.keys(docTypeInfo) as DocType[]).map((docType) => {
          const info = docTypeInfo[docType];
          const Icon = info.icon;
          const isActive = selectedDocType === docType;
          return (
            <button
              key={docType}
              className={`docgen-card ${isActive ? "active" : ""}`}
              onClick={() => generateDoc(docType)}
              disabled={docgenGenerating}
              style={{ borderColor: isActive ? info.color : undefined }}
            >
              <div className="docgen-card-icon" style={{ background: info.color }}>
                {docgenGenerating && isActive ? (
                  <Loader2 size={28} className="spin" />
                ) : (
                  <Icon size={28} />
                )}
              </div>
              <strong>{info.label}</strong>
              <p>{info.description}</p>
              {docgenGenerating && isActive ? (
                <span className="generating-label">
                  {isZh ? "生成中..." : "Generating..."}
                </span>
              ) : null}
            </button>
          );
        })}
      </div>

      {/* ── 测试文档进度条 ── */}
      {docgenGenerating && selectedDocType === "testing" ? (
        <div className="testing-progress">
          <div className="progress-header">
            <span className="progress-title">
              {isZh ? "测试文档生成中" : "Generating Testing Document"}
            </span>
            <span className="progress-step">
              {docgenCompletedSteps}/{testingSteps.length} {isZh ? "步" : "steps"}
            </span>
          </div>
          <div className="step-list">
            {testingSteps.map((step, i) => {
              const stepNum = i + 1;
              const done = docgenCompletedSteps > stepNum;
              const current = docgenCompletedSteps === stepNum;
              return (
                <div key={i} className={`step-item ${done ? "done" : current ? "current" : ""}`}>
                  <div className="step-indicator">
                    {done ? (
                      <CheckCircle2 size={16} color="#1f8a4c" />
                    ) : current ? (
                      <Loader2 size={16} className="spin" />
                    ) : (
                      <div className="step-dot" />
                    )}
                  </div>
                  <div className="step-text">
                    <span className="step-label">{step.label}</span>
                    <span className="step-sub">{step.sub}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

      {docgenError ? <div className="docgen-error">❌ {docgenError}</div> : null}

      {/* ── 文档生成结果 ── */}
      {docgenResult ? (
        <div className="docgen-result">
          <div className="result-header">
            <span>
              {isZh ? "生成完成" : "Generation Complete"} —{" "}
              {docTypeInfo[docgenResult.doc_type as DocType]?.label ?? docgenResult.doc_type}
              {reviewPassed
                ? isZh ? " ✅ 审核通过" : " ✅ Review Passed"
                : isZh
                  ? " ⚠️ 审核未完全通过"
                  : " ⚠️ Review Incomplete"}
            </span>
          </div>

          {tm ? (
            <div className="test-meta-bar">
              <MetaItem label={isZh ? "用例总数" : "Total"} value={tm.total} />
              <MetaItem label={isZh ? "通过" : "Passed"} value={tm.passed} color="#1f8a4c" />
              <MetaItem
                label={isZh ? "失败" : "Failed"}
                value={tm.failed}
                color={tm.failed > 0 ? "#dc2626" : undefined}
              />
              <MetaItem label={isZh ? "跳过" : "Skipped"} value={tm.skipped} color="#c86f1d" />
              <MetaItem label={isZh ? "通过率" : "Pass Rate"} value={`${passRate}%`} color={rateColor} large />
              <MetaItem label={isZh ? "执行日期" : "Date"} value={tm.report_date} />
            </div>
          ) : null}

          {docgenResult.storage_path ? (
            <div className="storage-info">
              {isZh ? "已保存至" : "Saved to"}: <code>{docgenResult.storage_path}</code>
            </div>
          ) : null}

          {docgenResult.review_report ? (
            <ReviewCard report={docgenResult.review_report as ReviewReport} isZh={isZh} />
          ) : null}

          <div className="doc-preview">
            <h3>{isZh ? "文档预览" : "Document Preview"}</h3>
            <div className="doc-preview-content">
              <MarkdownMessage
                content={
                  docgenResult.doc_final.length > 8000
                    ? docgenResult.doc_final.slice(0, 8000) + "\n\n*(预览截断)*"
                    : docgenResult.doc_final
                }
              />
            </div>
          </div>
        </div>
      ) : null}

      <style jsx>{`
        .docgen-panel {
          min-height: 0;
          overflow: auto;
          padding: 22px;
          display: grid;
          align-content: start;
          gap: 20px;
        }
        .docgen-header {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding-bottom: 16px;
          border-bottom: 1px solid var(--border);
        }
        .docgen-header strong {
          display: block;
          font-size: 18px;
          margin-bottom: 4px;
        }
        .docgen-subtitle {
          color: var(--muted);
          font-size: 13px;
          line-height: 1.5;
        }
        .docgen-cards {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 14px;
        }
        .docgen-card {
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
        .docgen-card:hover:not(:disabled) {
          box-shadow: 0 4px 16px rgba(23, 32, 42, 0.08);
          border-color: #aaa;
        }
        .docgen-card.active {
          box-shadow: 0 4px 20px rgba(23, 32, 42, 0.1);
        }
        .docgen-card:disabled { opacity: 0.7; cursor: not-allowed; }
        .docgen-card-icon {
          width: 52px;
          height: 52px;
          display: grid;
          place-items: center;
          border-radius: 12px;
          color: #fff;
        }
        .docgen-card strong { font-size: 15px; color: var(--text); }
        .docgen-card p { margin: 0; font-size: 12px; line-height: 1.5; color: var(--muted); }
        .generating-label { font-size: 12px; font-weight: 600; color: var(--active); }
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* progress */
        .testing-progress {
          border: 1px solid var(--border);
          border-radius: 10px;
          background: var(--panel);
          padding: 18px 20px;
          display: grid;
          gap: 14px;
        }
        .progress-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .progress-title { font-size: 14px; font-weight: 700; color: var(--text); }
        .progress-step { font-size: 12px; color: var(--muted); font-weight: 600; }
        .step-list { display: grid; gap: 0; }
        .step-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 8px 0;
          border-bottom: 1px solid #f0f2f5;
          color: var(--muted);
        }
        .step-item:last-child { border-bottom: 0; }
        .step-item.done { color: #1f8a4c; }
        .step-item.current { color: var(--text); }
        .step-indicator { width: 20px; display: grid; place-items: center; flex-shrink: 0; }
        .step-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--border);
        }
        .step-text { display: grid; gap: 2px; }
        .step-label { font-size: 13px; font-weight: 600; }
        .step-sub { font-size: 11px; color: var(--muted); }
        .step-item.done .step-sub { color: #1f8a4c; }

        /* errors */
        .docgen-error {
          background: #fef2f2;
          border: 1px solid #fca5a5;
          border-radius: 8px;
          padding: 12px;
          color: #dc2626;
          font-size: 13px;
        }

        /* results */
        .docgen-result { display: grid; gap: 14px; }
        .result-header {
          font-size: 14px;
          font-weight: 600;
          color: var(--text);
        }

        /* test meta bar */
        .test-meta-bar {
          display: flex;
          align-items: center;
          gap: 0;
          border: 1px solid var(--border);
          border-radius: 10px;
          background: var(--panel);
          overflow: hidden;
        }
        .meta-item {
          flex: 1;
          display: grid;
          gap: 3px;
          padding: 12px 16px;
          border-right: 1px solid var(--border);
          min-width: 0;
        }
        .meta-item:last-child { border-right: 0; }
        .meta-item.large { flex: 2; }
        .meta-label { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
        .meta-value { font-size: 18px; font-weight: 800; line-height: 1; }

        /* storage */
        .storage-info { font-size: 13px; color: var(--muted); }
        .storage-info code {
          background: #f6f8fb;
          border: 1px solid var(--border);
          border-radius: 4px;
          padding: 2px 6px;
          font-size: 12px;
        }

        /* preview */
        .doc-preview {
          border: 1px solid var(--border);
          border-radius: 8px;
          background: var(--panel);
          max-height: 600px;
          overflow: auto;
        }
        .doc-preview h3 {
          margin: 0;
          padding: 10px 14px;
          font-size: 13px;
          border-bottom: 1px solid var(--border);
          position: sticky;
          top: 0;
          background: var(--panel);
        }
        .doc-preview-content { padding: 14px; }

        /* review card */
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
        .review-summary {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          font-weight: 700;
        }
        .review-badge {
          font-size: 11px;
          font-weight: 700;
          border-radius: 4px;
          padding: 2px 8px;
        }
        .review-badge.pass { background: #edf8f1; color: #1f8a4c; }
        .review-badge.fail { background: #fef2f2; color: #dc2626; }
        .review-checks { display: grid; }
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
        .check-icon { display: grid; place-items: center; }
        .check-id { font-weight: 700; font-family: monospace; font-size: 11px; color: var(--muted); }
        .check-item { font-weight: 600; color: var(--text); }
        .check-detail {
          text-align: right;
          font-size: 11px;
          color: var(--muted);
          max-width: 220px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .review-check-row.failed .check-detail { color: #dc2626; font-weight: 600; }
      `}</style>
    </section>
  );
}

function ReviewCard({ report, isZh }: { report: ReviewReport; isZh: boolean }) {
  const sorted = [...report.checks].sort((a, b) =>
    a.passed === b.passed ? 0 : a.passed ? 1 : -1
  );
  const failCount = report.total_count - report.passed_count;

  return (
    <div className="review-card">
      <div className="review-card-header">
        <div className="review-summary">
          {report.passed ? (
            <CheckCircle2 size={18} color="#1f8a4c" />
          ) : (
            <AlertTriangle size={18} color="#dc2626" />
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

function MetaItem({
  label,
  value,
  color,
  large,
}: {
  label: string;
  value: string | number;
  color?: string;
  large?: boolean;
}) {
  return (
    <div className={`meta-item ${large ? "large" : ""}`}>
      <div className="meta-label">{label}</div>
      <div className="meta-value" style={{ color: color || undefined }}>
        {value}
      </div>
    </div>
  );
}
