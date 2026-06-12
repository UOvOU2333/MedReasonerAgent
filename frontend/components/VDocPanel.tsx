"use client";

import {
  AlertCircle, CheckCircle2, ChevronDown, ChevronUp, Database, ExternalLink, X,
  Download, FileArchive, FileText, Filter, Loader2, PlayCircle, RefreshCw,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { API_BASE } from "../lib/api";

type VDocItem = {
  name: string;
  type: string;
  version: string;
  created_at?: string;
  updated_at?: string;
  path: string;
  status: string;
  badges?: Record<string, VDocBadge>;
};

type VDocBadge = {
  status: "pass" | "fail" | "pending" | string;
  label: string;
  detail?: string;
};

type DocsResponse = {
  documents: VDocItem[];
  last_updated: string;
};

type ReplayCase = {
  index: number;
  expected: Record<string, unknown>;
  actual: Record<string, unknown>;
  passed: boolean;
  error: string;
};

type ReplayReport = {
  total: number;
  passed: number;
  failed: number;
  pass_rate: number;
  cases: ReplayCase[];
};

type PdfPreview = {
  pdf_url: string;
  pdf_path?: string;
};

type TestRunReport = {
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  pass_rate: number;
};

type DemoStep = {
  key: string;
  label: string;
  status: "pending" | "running" | "passed" | "failed";
};

type DemoResult = {
  storage_path: string;
  review_summary: string;
  review_passed: boolean;
  pdf_url: string;
  replay: ReplayReport;
  pytest: TestRunReport;
};

const demoStepLabels = [
  { key: "generate", label: "生成测试用例文档" },
  { key: "render", label: "渲染 PDF 预览" },
  { key: "replay", label: "真实入组回放" },
  { key: "pytest", label: "生成测试执行数据" },
  { key: "index", label: "刷新文档索引" },
];

const filterOptions = [
  { key: "all", label: "全部" },
  { key: "requirements", label: "需求文档" },
  { key: "architecture", label: "架构文档" },
  { key: "testing", label: "测试文档" },
  { key: "tc_normal", label: "正常用例" },
  { key: "tc_boundary", label: "边界用例" },
  { key: "tc_abnormal", label: "异常用例" },
] as const;

const typeLabels: Record<string, string> = {
  requirements: "需求文档",
  architecture: "架构文档",
  testing: "测试文档",
  tc_normal: "正常场景测试用例",
  tc_boundary: "边界场景测试用例",
  tc_abnormal: "异常场景测试用例",
};

export default function VDocPanel() {
  const [docs, setDocs] = useState<VDocItem[]>([]);
  const [lastUpdated, setLastUpdated] = useState("");
  const [filter, setFilter] = useState<(typeof filterOptions)[number]["key"]>("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<VDocItem | null>(null);
  const [pdfPreview, setPdfPreview] = useState<PdfPreview | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfDrawerOpen, setPdfDrawerOpen] = useState(true);
  const [pdfEmbedEnabled, setPdfEmbedEnabled] = useState(false);
  const [replayReport, setReplayReport] = useState<ReplayReport | null>(null);
  const [replayLoading, setReplayLoading] = useState(false);
  const [replayModalOpen, setReplayModalOpen] = useState(false);
  const [demoRunning, setDemoRunning] = useState(false);
  const [demoSteps, setDemoSteps] = useState<DemoStep[]>(
    demoStepLabels.map((step) => ({ ...step, status: "pending" })),
  );
  const [demoResult, setDemoResult] = useState<DemoResult | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    void loadDocs();
  }, []);

  const filteredDocs = useMemo(() => {
    if (filter === "all") return docs;
    if (filter === "testing") {
      return docs.filter((doc) => doc.type === "testing" || doc.type.startsWith("tc_"));
    }
    return docs.filter((doc) => doc.type === filter);
  }, [docs, filter]);

  async function loadDocs() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/docgen/docs`);
      if (!response.ok) throw new Error(`Load docs failed: ${response.status}`);
      const data = (await response.json()) as DocsResponse;
      setDocs(data.documents ?? []);
      setLastUpdated(data.last_updated ?? "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function previewPdf(doc: VDocItem) {
    setSelected(doc);
    setPdfLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/docgen/render`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ storage_path: doc.path, output_name: filenameFromPath(doc.path).replace(/\.md$/, "") }),
      });
      if (!response.ok) throw new Error(`Render failed: ${response.status}`);
      const rendered = (await response.json()) as PdfPreview;
      setPdfPreview(rendered);
      setPdfDrawerOpen(false);
      window.open(pdfUrl(rendered.pdf_url), "_blank", "noopener,noreferrer");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setPdfLoading(false);
    }
  }

  async function runReplay(doc: VDocItem) {
    setSelected(doc);
    setReplayLoading(true);
    setReplayModalOpen(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/testing/replay-doc`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ storage_path: doc.path }),
      });
      if (!response.ok) throw new Error(`Replay failed: ${response.status}`);
      setReplayReport(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setReplayLoading(false);
    }
  }

  function markDemoStep(key: string, status: DemoStep["status"]) {
    setDemoSteps((steps) => steps.map((step) => (step.key === key ? { ...step, status } : step)));
  }

  async function runAcceptanceDemo() {
    setDemoRunning(true);
    setDemoResult(null);
    setError(null);
    setReplayReport(null);
    setReplayModalOpen(false);
    setDemoSteps(demoStepLabels.map((step) => ({ ...step, status: "pending" })));

    try {
      markDemoStep("generate", "running");
      const generateResponse = await fetch(`${API_BASE}/tcgen/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: "生成正常场景测试用例",
          language: "zh",
          mode: "tcgen",
          tc_type: "normal",
          project_name: "MedReasonerAgent",
        }),
      });
      if (!generateResponse.ok) throw new Error(`Generate failed: ${generateResponse.status}`);
      const generated = await generateResponse.json();
      const storagePath = String(generated.storage_path || "");
      if (!storagePath) throw new Error("Generated document has no storage_path");
      markDemoStep("generate", "passed");

      markDemoStep("render", "running");
      const renderResponse = await fetch(`${API_BASE}/docgen/render`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ storage_path: storagePath, output_name: "vdoc_acceptance_demo" }),
      });
      if (!renderResponse.ok) throw new Error(`Render failed: ${renderResponse.status}`);
      const rendered = (await renderResponse.json()) as PdfPreview;
      setPdfPreview(rendered);
      setPdfDrawerOpen(true);
      markDemoStep("render", "passed");

      markDemoStep("replay", "running");
      const replayResponse = await fetch(`${API_BASE}/testing/replay-doc`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ storage_path: storagePath }),
      });
      if (!replayResponse.ok) throw new Error(`Replay failed: ${replayResponse.status}`);
      const replay = (await replayResponse.json()) as ReplayReport;
      setReplayReport(replay);
      markDemoStep("replay", "passed");

      markDemoStep("pytest", "running");
      const pytestResponse = await fetch(`${API_BASE}/testing/run`);
      if (!pytestResponse.ok) throw new Error(`Pytest run failed: ${pytestResponse.status}`);
      const pytestReport = (await pytestResponse.json()) as TestRunReport;
      markDemoStep("pytest", "passed");

      markDemoStep("index", "running");
      await loadDocs();
      setFilter("tc_normal");
      markDemoStep("index", "passed");

      const review = generated.review_report as Record<string, unknown> | undefined;
      setDemoResult({
        storage_path: storagePath,
        review_summary: String(review?.summary ?? "-"),
        review_passed: review?.passed === true,
        pdf_url: rendered.pdf_url,
        replay,
        pytest: pytestReport,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setDemoSteps((steps) =>
        steps.map((step) => (step.status === "running" ? { ...step, status: "failed" } : step)),
      );
    } finally {
      setDemoRunning(false);
    }
  }

  async function exportPackage() {
    setExporting(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/docgen/export-package`);
      if (!response.ok) throw new Error(`Export failed: ${response.status}`);
      const blob = await response.blob();
      const disposition = response.headers.get("content-disposition") || "";
      const match = disposition.match(/filename="?([^";]+)"?/i);
      const filename = match?.[1] || `MedReasonerAgent_delivery_${Date.now()}.zip`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setExporting(false);
    }
  }

  return (
    <section className="vdoc-panel">
      <div className="vdoc-hero">
        <div className="vdoc-title">
          <div className="vdoc-icon"><Database size={24} /></div>
          <div>
            <h2>虚拟文档管理智能体</h2>
            <p>统一管理生成文档的接收、校验、元数据、存储、索引、预览与验收。</p>
          </div>
        </div>
        <div className="hero-actions">
          <button className="primary-btn" onClick={runAcceptanceDemo} disabled={demoRunning}>
            {demoRunning ? <Loader2 size={15} className="spin" /> : <PlayCircle size={15} />}
            一键验收演示
          </button>
          <button className="ghost-btn" onClick={exportPackage} disabled={exporting || demoRunning}>
            {exporting ? <Loader2 size={15} className="spin" /> : <Download size={15} />}
            导出交付包
          </button>
          <button className="ghost-btn" onClick={loadDocs} disabled={loading || demoRunning}>
            {loading ? <Loader2 size={15} className="spin" /> : <RefreshCw size={15} />}
            刷新索引
          </button>
        </div>
      </div>

      <div className="pipeline">
        {["Receiver", "Validator", "Tagger", "Storer", "Notifier"].map((item, index) => (
          <div className="pipeline-item" key={item}>
            <span className="pipeline-index">{index + 1}</span>
            <strong>{item}</strong>
          </div>
        ))}
      </div>

      <section className="demo-panel">
        <div className="demo-header">
          <strong>端到端验收演示</strong>
          <span>测试用例生成 → 虚拟文档存储 → PDF → 回放 → pytest</span>
        </div>
        <div className="demo-steps">
          {demoSteps.map((step) => (
            <div className={`demo-step ${step.status}`} key={step.key}>
              <StepIcon status={step.status} />
              <span>{step.label}</span>
            </div>
          ))}
        </div>
        {demoResult ? (
          <div className="demo-result">
            <div>
              <span>文档审核</span>
              <strong className={demoResult.review_passed ? "pass" : "fail"}>{demoResult.review_summary}</strong>
            </div>
            <div>
              <span>入组回放</span>
              <strong className={demoResult.replay.failed === 0 ? "pass" : "fail"}>
                {demoResult.replay.passed}/{demoResult.replay.total} 通过 ({demoResult.replay.pass_rate}%)
              </strong>
            </div>
            <div>
              <span>pytest</span>
              <strong className={demoResult.pytest.failed === 0 ? "pass" : "fail"}>
                {demoResult.pytest.passed}/{demoResult.pytest.total} 通过 ({demoResult.pytest.pass_rate}%)
              </strong>
            </div>
            <div>
              <span>保存路径</span>
              <strong title={demoResult.storage_path}>{demoResult.storage_path}</strong>
            </div>
          </div>
        ) : null}
      </section>

      <div className="toolbar">
        <div className="filter-label"><Filter size={14} /> 文档类型</div>
        <div className="filters">
          {filterOptions.map((option) => (
            <button
              key={option.key}
              className={filter === option.key ? "active" : ""}
              onClick={() => setFilter(option.key)}
            >
              {option.label}
            </button>
          ))}
        </div>
        <span className="index-time">索引更新时间：{formatDate(lastUpdated) || "-"}</span>
      </div>

      {error ? (
        <div className="error-box"><AlertCircle size={16} /> {error}</div>
      ) : null}

      {loading ? (
        <div className="empty-state"><Loader2 size={20} className="spin" /> 正在加载文档索引...</div>
      ) : filteredDocs.length === 0 ? (
        <div className="empty-state">
          <FileArchive size={24} />
          暂无文档，请先在文档生成或测试用例生成中生成文档。
        </div>
      ) : (
        <div className="doc-grid">
          {filteredDocs.map((doc) => (
            <article className="doc-card" key={`${doc.name}-${doc.type}-${doc.version}-${doc.path}`}>
              <div className="doc-card-head">
                <div className="doc-type-icon"><FileText size={18} /></div>
                <div>
                  <h3>{doc.name}</h3>
                  <span>{typeLabels[doc.type] ?? doc.type}</span>
                </div>
                <StatusBadge status={doc.status} />
              </div>
              <div className="doc-meta">
                <div><span>版本</span><strong>{doc.version}</strong></div>
                <div><span>更新时间</span><strong>{formatDate(doc.updated_at)}</strong></div>
              </div>
              <div className="doc-path" title={doc.path}>{doc.path}</div>
              <div className="doc-badges">
                {badgeList(doc).map((badge) => (
                  <span
                    className={`doc-badge ${badge.status}`}
                    title={badge.detail || badge.label}
                    key={`${doc.path}-${badge.label}`}
                  >
                    {badge.status === "pass" ? <CheckCircle2 size={12} /> : <AlertCircle size={12} />}
                    {badge.label}
                  </span>
                ))}
              </div>
              <div className="doc-actions">
                <button onClick={() => previewPdf(doc)} disabled={pdfLoading}>
                  {pdfLoading && selected?.path === doc.path ? <Loader2 size={14} className="spin" /> : null}
                  PDF 预览
                </button>
                {isTestCaseDoc(doc) ? (
                  <button onClick={() => runReplay(doc)} disabled={replayLoading}>
                    {replayLoading && selected?.path === doc.path ? <Loader2 size={14} className="spin" /> : <PlayCircle size={14} />}
                    真实入组回放
                  </button>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      )}

      {pdfPreview ? (
        <section className={`preview-panel ${pdfDrawerOpen ? "" : "collapsed"}`}>
          <div className="preview-header">
            <strong>PDF 预览{selected ? ` - ${typeLabels[selected.type] ?? selected.type}` : ""}</strong>
            <div className="preview-actions">
              <button
                type="button"
                data-testid="vdoc-pdf-embed-toggle"
                onClick={() => setPdfEmbedEnabled((enabled) => !enabled)}
              >
                {pdfEmbedEnabled ? "禁用内嵌预览" : "启用内嵌预览"}
              </button>
              <button
                type="button"
                data-testid="vdoc-pdf-toggle"
                onClick={() => setPdfDrawerOpen((open) => !open)}
              >
                {pdfDrawerOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                {pdfDrawerOpen ? "收起" : "打开预览"}
              </button>
              <a href={pdfUrl(pdfPreview.pdf_url)} target="_blank" rel="noreferrer">
                <ExternalLink size={14} /> 打开 PDF
              </a>
            </div>
          </div>
          {pdfDrawerOpen ? (
            pdfEmbedEnabled ? (
              <div className="pdf-frame-wrap">
                <iframe src={pdfSrc(pdfPreview.pdf_url)} title="VDoc PDF preview" />
              </div>
            ) : (
              <div className="pdf-placeholder">
                <FileText size={20} />
                <div>
                  <strong>PDF 已生成</strong>
                  <span>Edge 会拦截内嵌 PDF 的滚轮。默认关闭内嵌预览，使用“打开 PDF”查看最稳定。</span>
                </div>
              </div>
            )
          ) : null}
        </section>
      ) : null}

      {replayReport ? (
        <div className={`replay-modal-layer ${replayModalOpen ? "open" : ""}`}>
          <button
            type="button"
            className="replay-backdrop"
            aria-label="关闭真实入组回放结果"
            onClick={() => setReplayModalOpen(false)}
          />
          <section className="replay-modal" role="dialog" aria-modal="true" aria-label="真实入组回放结果">
            <div className="replay-modal-header">
              <div>
                <strong>真实入组回放结果</strong>
                <span>{selected ? `${typeLabels[selected.type] ?? selected.type} · ` : ""}{replayReport.passed}/{replayReport.total} 通过 ({replayReport.pass_rate}%)</span>
              </div>
              <button type="button" onClick={() => setReplayModalOpen(false)} aria-label="关闭">
                <X size={16} />
              </button>
            </div>
            <div className="replay-table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>实际 DRG</th>
                    <th>期望 DRG</th>
                    <th>状态</th>
                    <th>说明</th>
                  </tr>
                </thead>
                <tbody>
                  {replayReport.cases.map((item) => (
                    <tr key={item.index}>
                      <td>{item.index}</td>
                      <td>{formatDrg(item.actual)}</td>
                      <td>{formatDrg(item.expected)}</td>
                      <td className={item.passed ? "pass" : "fail"}>{item.passed ? "通过" : "失败"}</td>
                      <td>{item.error || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      ) : null}

      <style jsx>{`
        .vdoc-panel {
          min-height: 0;
          overflow: auto;
          padding: 22px 22px 96px;
          display: grid;
          align-content: start;
          gap: 16px;
          overscroll-behavior: contain;
        }
        .vdoc-hero {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          border: 1px solid var(--border);
          border-radius: 10px;
          background: var(--panel);
          padding: 16px 18px;
        }
        .vdoc-title {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .vdoc-icon {
          width: 44px;
          height: 44px;
          display: grid;
          place-items: center;
          border-radius: 10px;
          background: #eef8f5;
          color: var(--accent);
        }
        .vdoc-title h2 {
          margin: 0 0 4px;
          font-size: 18px;
        }
        .vdoc-title p {
          margin: 0;
          color: var(--muted);
          font-size: 13px;
        }
        .hero-actions {
          display: flex;
          align-items: center;
          gap: 8px;
          flex-wrap: wrap;
          justify-content: flex-end;
        }
        .primary-btn,
        .ghost-btn,
        .doc-actions button,
        .preview-actions button,
        .preview-actions a {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          border: 1px solid var(--border);
          border-radius: 7px;
          background: #fff;
          color: var(--text);
          padding: 7px 10px;
          font-size: 12px;
          font-weight: 700;
          cursor: pointer;
          text-decoration: none;
        }
        .primary-btn {
          background: #1f8a4c;
          border-color: #1f8a4c;
          color: #fff;
        }
        .primary-btn:hover {
          background: #18733f;
        }
        .ghost-btn:hover,
        .doc-actions button:hover,
        .preview-actions button:hover,
        .preview-actions a:hover {
          background: #eef1f5;
        }
        button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        .spin,
        :global(.spin) {
          animation: spin 1s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .pipeline {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          border: 1px solid var(--border);
          border-radius: 10px;
          background: var(--panel);
          overflow: hidden;
        }
        .pipeline-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 11px 12px;
          border-right: 1px solid var(--border);
          font-size: 12px;
        }
        .pipeline-item:last-child {
          border-right: 0;
        }
        .pipeline-index {
          width: 20px;
          height: 20px;
          display: grid;
          place-items: center;
          border-radius: 50%;
          background: #1f8a4c;
          color: #fff;
          font-size: 11px;
          font-weight: 800;
        }
        .demo-panel {
          border: 1px solid var(--border);
          border-radius: 10px;
          background: var(--panel);
          padding: 14px;
          display: grid;
          gap: 12px;
        }
        .demo-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          font-size: 13px;
        }
        .demo-header strong {
          font-size: 14px;
        }
        .demo-header span {
          color: var(--muted);
          font-size: 12px;
        }
        .demo-steps {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 8px;
        }
        .demo-step {
          display: flex;
          align-items: center;
          gap: 7px;
          border: 1px solid #eef1f5;
          border-radius: 8px;
          padding: 8px;
          color: var(--muted);
          font-size: 12px;
          font-weight: 700;
          min-width: 0;
        }
        .demo-step span {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .demo-step.running {
          color: #c86f1d;
          background: #fffaf4;
          border-color: #f1d4b8;
        }
        .demo-step.passed {
          color: #1f8a4c;
          background: #f0f8f4;
          border-color: #d9eadf;
        }
        .demo-step.failed {
          color: #dc2626;
          background: #fef2f2;
          border-color: #fca5a5;
        }
        :global(.pending-dot) {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #cbd5e1;
          flex: 0 0 auto;
        }
        .demo-result {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 8px;
        }
        .demo-result div {
          display: grid;
          gap: 4px;
          border: 1px solid #eef1f5;
          border-radius: 8px;
          background: #f8fafc;
          padding: 9px;
          min-width: 0;
        }
        .demo-result span {
          color: var(--muted);
          font-size: 10px;
          font-weight: 800;
        }
        .demo-result strong {
          color: var(--text);
          font-size: 12px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .toolbar {
          display: flex;
          align-items: center;
          gap: 10px;
          flex-wrap: wrap;
        }
        .filter-label {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          font-weight: 800;
          color: var(--muted);
        }
        .filters {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }
        .filters button {
          border: 1px solid var(--border);
          border-radius: 999px;
          background: #fff;
          padding: 5px 10px;
          color: var(--muted);
          font-size: 12px;
          font-weight: 700;
          cursor: pointer;
        }
        .filters button.active {
          background: #1f8a4c;
          border-color: #1f8a4c;
          color: #fff;
        }
        .index-time {
          margin-left: auto;
          color: var(--muted);
          font-size: 12px;
        }
        .error-box,
        .empty-state {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          border: 1px solid var(--border);
          border-radius: 10px;
          background: var(--panel);
          min-height: 96px;
          color: var(--muted);
          font-size: 13px;
        }
        .error-box {
          min-height: auto;
          justify-content: flex-start;
          border-color: #fca5a5;
          background: #fef2f2;
          color: #dc2626;
          padding: 12px;
        }
        .doc-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
          gap: 12px;
        }
        .doc-card {
          border: 1px solid var(--border);
          border-radius: 10px;
          background: var(--panel);
          padding: 14px;
          display: grid;
          gap: 12px;
        }
        .doc-card-head {
          display: grid;
          grid-template-columns: auto 1fr auto;
          gap: 10px;
          align-items: start;
        }
        .doc-type-icon {
          width: 34px;
          height: 34px;
          display: grid;
          place-items: center;
          border-radius: 8px;
          background: #f1f5f9;
          color: var(--accent);
        }
        .doc-card h3 {
          margin: 0 0 3px;
          font-size: 14px;
        }
        .doc-card-head span {
          color: var(--muted);
          font-size: 12px;
        }
        :global(.status-badge) {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          border-radius: 999px;
          background: #edf8f1;
          color: #1f8a4c;
          padding: 3px 8px;
          font-size: 11px;
          font-weight: 800;
        }
        .doc-meta {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
        }
        .doc-meta div {
          display: grid;
          gap: 2px;
          border: 1px solid #eef1f5;
          border-radius: 7px;
          padding: 7px 8px;
          min-width: 0;
        }
        .doc-meta span {
          color: var(--muted);
          font-size: 10px;
          font-weight: 800;
        }
        .doc-meta strong {
          color: var(--text);
          font-size: 12px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .doc-path {
          border: 1px solid #eef1f5;
          border-radius: 7px;
          background: #f8fafc;
          padding: 6px 8px;
          color: var(--muted);
          font-size: 11px;
          font-family: Consolas, monospace;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .doc-badges {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }
        .doc-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          min-height: 24px;
          border: 1px solid #e2e8f0;
          border-radius: 999px;
          background: #f8fafc;
          color: var(--muted);
          padding: 3px 8px;
          font-size: 11px;
          font-weight: 800;
          max-width: 100%;
        }
        .doc-badge.pass {
          border-color: #b7e1c5;
          background: #effaf3;
          color: #1f8a4c;
        }
        .doc-badge.fail {
          border-color: #fecaca;
          background: #fef2f2;
          color: #dc2626;
        }
        .doc-badge.pending {
          border-color: #f1d4b8;
          background: #fffaf4;
          color: #c86f1d;
        }
        .doc-actions {
          display: flex;
          flex-wrap: wrap;
          gap: 7px;
        }
        .preview-panel,
        .replay-modal {
          border: 1px solid var(--border);
          border-radius: 10px;
          background: var(--panel);
          overflow: hidden;
          min-width: 0;
        }
        .preview-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          padding: 11px 14px;
          border-bottom: 1px solid var(--border);
          background: #fafbfc;
          font-size: 13px;
        }
        .preview-actions {
          display: flex;
          align-items: center;
          gap: 8px;
          flex-wrap: wrap;
          justify-content: flex-end;
        }
        .preview-actions span {
          color: var(--muted);
          font-size: 12px;
          font-weight: 800;
        }
        .pdf-frame-wrap {
          height: min(70vh, 720px);
          min-height: 420px;
          overflow: auto;
          background: #f8fafc;
          overscroll-behavior: contain;
        }
        .pdf-placeholder {
          display: flex;
          align-items: center;
          gap: 10px;
          min-height: 96px;
          padding: 18px;
          background: #f8fafc;
          color: var(--muted);
          font-size: 13px;
        }
        .pdf-placeholder div {
          display: grid;
          gap: 4px;
        }
        .pdf-placeholder strong {
          color: var(--text);
          font-size: 14px;
        }
        .pdf-placeholder span {
          line-height: 1.5;
        }
        .preview-panel iframe {
          width: 100%;
          height: 100%;
          min-height: 420px;
          border: 0;
          display: block;
          background: #f8fafc;
        }
        .preview-panel.collapsed,
        .replay-modal.collapsed {
          background: #fafbfc;
        }
        .replay-modal-layer {
          position: fixed;
          inset: 0;
          z-index: 80;
          display: none;
          align-items: center;
          justify-content: center;
          padding: 28px;
        }
        .replay-modal-layer.open {
          display: flex;
        }
        .replay-backdrop {
          position: absolute;
          inset: 0;
          border: 0;
          background: rgba(15, 23, 42, 0.38);
          cursor: pointer;
        }
        .replay-modal {
          position: relative;
          width: min(980px, calc(100vw - 56px));
          max-height: min(720px, calc(100vh - 56px));
          display: grid;
          grid-template-rows: auto 1fr;
          box-shadow: 0 24px 70px rgba(15, 23, 42, 0.22);
        }
        .replay-modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          padding: 13px 15px;
          border-bottom: 1px solid var(--border);
          background: #fafbfc;
        }
        .replay-modal-header div {
          display: grid;
          gap: 3px;
          min-width: 0;
        }
        .replay-modal-header strong {
          color: var(--text);
          font-size: 14px;
        }
        .replay-modal-header span {
          color: var(--muted);
          font-size: 12px;
          font-weight: 800;
        }
        .replay-modal-header button {
          width: 34px;
          height: 34px;
          display: grid;
          place-items: center;
          border: 1px solid var(--border);
          border-radius: 8px;
          background: #fff;
          color: var(--text);
          cursor: pointer;
        }
        .replay-modal-header button:hover {
          background: #eef1f5;
        }
        .replay-table-wrap {
          overflow: auto;
          max-height: calc(min(720px, 100vh - 56px) - 62px);
        }
        .replay-modal table {
          width: 100%;
          min-width: 720px;
          border-collapse: collapse;
          font-size: 12px;
        }
        .replay-modal th,
        .replay-modal td {
          border-bottom: 1px solid #eef1f5;
          padding: 8px 10px;
          text-align: left;
          vertical-align: top;
        }
        .replay-modal th {
          color: var(--muted);
          background: #fbfcfd;
          position: sticky;
          top: 0;
          z-index: 1;
        }
        .pass {
          color: #1f8a4c;
          font-weight: 800;
        }
        .fail {
          color: #dc2626;
          font-weight: 800;
        }
        @media (max-width: 980px) {
          .demo-steps,
          .demo-result,
          .pipeline {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
        }
      `}</style>
    </section>
  );
}

function StepIcon({ status }: { status: DemoStep["status"] }) {
  if (status === "running") return <Loader2 size={14} className="spin" />;
  if (status === "passed") return <CheckCircle2 size={14} />;
  if (status === "failed") return <AlertCircle size={14} />;
  return <span className="pending-dot" />;
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span className="status-badge">
      <CheckCircle2 size={12} />
      {status || "stored"}
    </span>
  );
}

function filenameFromPath(path: string) {
  return path.replace(/\\/g, "/").split("/").pop() || path;
}

function isTestCaseDoc(doc: VDocItem) {
  return doc.type.startsWith("tc_");
}

function badgeList(doc: VDocItem) {
  const badges = doc.badges ?? {};
  return [badges.content_review, badges.pdf, badges.replay].filter(Boolean) as VDocBadge[];
}

function pdfUrl(url: string) {
  return url.startsWith("http") ? url : `${API_BASE}${url}`;
}

function pdfSrc(url: string) {
  return `${pdfUrl(url)}#toolbar=1&navpanes=0&view=FitH`;
}

function formatDate(value?: string) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDrg(value: Record<string, unknown>) {
  const parts = ["mdc", "adrg", "drg", "complication"]
    .filter((key) => value?.[key] !== undefined)
    .map((key) => `${key.toUpperCase()}: ${String(value[key])}`);
  return parts.length ? parts.join(" / ") : "-";
}
