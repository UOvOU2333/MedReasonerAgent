"use client";

import { Bot, FileText, FileCode, ClipboardCheck, Download, Loader2, CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import { useState } from "react";
import { useTraceStore } from "../store/traceStore";
import { API_BASE } from "../lib/api";
import MarkdownMessage from "./MarkdownMessage";

type DocType = "requirements" | "architecture" | "testing";

// 审核报告中每条检查的数据结构
type ReviewCheck = {
  check: string;   // CHK-01, CHK-02, ...
  item: string;    // 检查项名称
  passed: boolean;
  detail: string;  // 通过/失败详情
};

type ReviewReport = {
  passed: boolean;
  passed_count: number;
  total_count: number;
  checks: ReviewCheck[];
  summary: string;
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
      "生成完整的测试方案文档，含测试策略、单元/集成/系统/验收测试方案、测试环境和缺陷管理。",
    color: "#c86f1d",
  },
};

export default function DocGenPanel() {
  const [selectedDocType, setSelectedDocType] = useState<DocType | null>(null);
  const [generating, setGenerating] = useState(false);
  const [docResult, setDocResult] = useState<{
    answer: string;
    doc_final: string;
    doc_type: string;
    storage_path: string;
    review_report: Record<string, unknown>;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const language = useTraceStore((state) => state.language);
  const isZh = language === "zh";

  async function generateDoc(docType: DocType) {
    setSelectedDocType(docType);
    setGenerating(true);
    setError(null);
    setDocResult(null);

    const queryMap: Record<DocType, string> = {
      requirements: isZh ? "生成需求分析文档" : "Generate requirements analysis document",
      architecture: isZh ? "生成架构设计文档" : "Generate architecture design document",
      testing: isZh ? "生成测试文档" : "Generate test plan document",
    };

    try {
      const response = await fetch(`${API_BASE}/docgen/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: queryMap[docType],
          language,
          mode: "docgen",
          doc_type: docType,
          project_name: "MedReasonerAgent",
        }),
      });

      if (!response.ok) {
        throw new Error(`Generate failed: ${response.status}`);
      }
      const data = await response.json();
      setDocResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setGenerating(false);
    }
  }

  function downloadDoc() {
    if (!docResult?.doc_final) return;
    const blob = new Blob([docResult.doc_final], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const docType = docResult.doc_type || "requirements";
    a.href = url;
    a.download = `MedReasonerAgent_${docType}_V1.0.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const reviewPassed = docResult?.review_report
    ? (docResult.review_report as Record<string, unknown>).passed === true
    : false;

  return (
    <section className="docgen-panel">
      <div className="docgen-header">
        <Bot size={20} />
        <div>
          <strong>{isZh ? "文档自动生成智能体" : "Document Generation Agent"}</strong>
          <span className="docgen-subtitle">
            {isZh ? "选择文档类型，智能体将自动分析项目并生成符合规范的文档" : "Select document type to auto-generate specification-compliant documentation"}
          </span>
        </div>
      </div>

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
              disabled={generating}
              style={{ borderColor: isActive ? info.color : undefined }}
            >
              <div className="docgen-card-icon" style={{ background: info.color }}>
                {generating && isActive ? <Loader2 size={28} className="spin" /> : <Icon size={28} />}
              </div>
              <strong>{info.label}</strong>
              <p>{info.description}</p>
              {generating && isActive ? (
                <span className="generating-label">{isZh ? "生成中..." : "Generating..."}</span>
              ) : null}
            </button>
          );
        })}
      </div>

      {error ? <div className="docgen-error">❌ {error}</div> : null}

      {docResult ? (
        <div className="docgen-result">
          <div className="result-header">
            <span>
              {isZh ? "生成完成" : "Generation Complete"} — {docTypeInfo[docResult.doc_type as DocType]?.label ?? docResult.doc_type}
              {" "}
              {reviewPassed
                ? isZh ? "✅ 审核通过" : "✅ Review Passed"
                : isZh ? "⚠️ 审核未完全通过" : "⚠️ Review Incomplete"}
            </span>
            <button className="download-btn" onClick={downloadDoc} title={isZh ? "下载文档" : "Download document"}>
              <Download size={16} /> {isZh ? "下载 .md" : "Download .md"}
            </button>
          </div>

          {docResult.storage_path ? (
            <div className="storage-info">
              {isZh ? "已保存至" : "Saved to"}: <code>{docResult.storage_path}</code>
            </div>
          ) : null}

          {docResult.review_report ? (
            <ReviewCard
              report={docResult.review_report as ReviewReport}
              isZh={isZh}
            />
          ) : null}

          <div className="doc-preview">
            <h3>{isZh ? "文档预览" : "Document Preview"}</h3>
            <div className="doc-preview-content">
              <MarkdownMessage content={docResult.doc_final.slice(0, 5000) + (docResult.doc_final.length > 5000 ? "\n\n*(预览截断，下载完整文档)*" : "")} />
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
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
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
        .docgen-card:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }
        .docgen-card-icon {
          width: 52px;
          height: 52px;
          display: grid;
          place-items: center;
          border-radius: 12px;
          color: #fff;
        }
        .docgen-card strong {
          font-size: 15px;
          color: var(--text);
        }
        .docgen-card p {
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
        .docgen-error {
          background: #fef2f2;
          border: 1px solid #fca5a5;
          border-radius: 8px;
          padding: 12px;
          color: #dc2626;
          font-size: 13px;
        }
        .docgen-result {
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
        .doc-preview {
          border: 1px solid var(--border);
          border-radius: 8px;
          background: var(--panel);
          max-height: 520px;
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
        .doc-preview-content {
          padding: 14px;
        }
      `}</style>
    </section>
  );
}


// ── 审核报告卡片（直接可见，逐项展示通过/失败） ──

function ReviewCard({ report, isZh }: { report: ReviewReport; isZh: boolean }) {
  // 失败项排前面
  const sorted = [...report.checks].sort((a, b) => (a.passed === b.passed ? 0 : a.passed ? 1 : -1));
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
