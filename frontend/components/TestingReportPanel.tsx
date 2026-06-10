"use client";

import {
  Bot, Play, FileText, Download, Loader2, CheckCircle2, XCircle,
  AlertTriangle, BarChart3, RefreshCw,
} from "lucide-react";
import { useState } from "react";
import { useTraceStore } from "../store/traceStore";
import { API_BASE } from "../lib/api";
import MarkdownMessage from "./MarkdownMessage";

type TestData = {
  report_date: string;
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  error: number;
  pass_rate: number;
  exit_code: number;
};

export default function TestingReportPanel() {
  const [testingRun, setTestingRun] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [testData, setTestData] = useState<TestData | null>(null);
  const [reportContent, setReportContent] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const language = useTraceStore((s) => s.language);
  const isZh = language === "zh";

  async function runTests() {
    setTestingRun(true);
    setError(null);
    setTestData(null);
    setReportContent("");

    try {
      const resp = await fetch(`${API_BASE}/testing/run`);
      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(`${resp.status}: ${text}`);
      }
      const data = await resp.json();
      setTestData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setTestingRun(false);
    }
  }

  async function generateReport() {
    if (!testData) return;
    setGeneratingReport(true);
    setError(null);

    try {
      const resp = await fetch(`${API_BASE}/testing/report?language=${language}`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(testData),
      });
      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(`${resp.status}: ${text}`);
      }
      const data = await resp.json();
      setReportContent(data.report);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setGeneratingReport(false);
    }
  }

  function downloadReport() {
    if (!reportContent) return;
    const blob = new Blob([reportContent], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `MedReasonerAgent_test_report_${testData?.report_date ?? "v1"}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const passRate = testData?.pass_rate ?? 0;
  const rateColor = passRate >= 80 ? "#1f8a4c" : passRate >= 50 ? "#c86f1d" : "#dc2626";

  return (
    <section className="testing-panel">
      <div className="panel-header">
        <Bot size={20} />
        <div>
          <strong>{isZh ? "测试执行报告" : "Test Execution Report"}</strong>
          <span className="panel-subtitle">
            {isZh
              ? "运行 pytest 测试用例，收集执行结果，由大模型生成结构化测试报告"
              : "Run pytest, collect results, and generate a structured test report via LLM"}
          </span>
        </div>
      </div>

      <div className="action-bar">
        <button className="run-btn" onClick={runTests} disabled={testingRun || generatingReport}>
          {testingRun ? <Loader2 size={16} className="spin" /> : <Play size={16} />}
          {testingRun
            ? isZh ? "运行测试中..." : "Running tests..."
            : isZh ? "运行测试" : "Run Tests"}
        </button>

        {testData && !reportContent ? (
          <button className="report-btn" onClick={generateReport} disabled={generatingReport}>
            {generatingReport ? <Loader2 size={16} className="spin" /> : <FileText size={16} />}
            {generatingReport
              ? isZh ? "生成报告中..." : "Generating report..."
              : isZh ? "生成 LLM 报告" : "Generate LLM Report"}
          </button>
        ) : null}

        {reportContent ? (
          <button className="download-btn" onClick={downloadReport}>
            <Download size={16} />
            {isZh ? "下载报告" : "Download Report"}
          </button>
        ) : null}
      </div>

      {error ? (
        <div className="error-box">
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      ) : null}

      {testData ? (
        <div className="test-summary">
          <div className="summary-grid">
            <StatCard label={isZh ? "用例总数" : "Total"} value={testData.total} icon={<BarChart3 size={18} />} />
            <StatCard label={isZh ? "通过" : "Passed"} value={testData.passed} icon={<CheckCircle2 size={18} />} color="#1f8a4c" />
            <StatCard label={isZh ? "失败" : "Failed"} value={testData.failed} icon={<XCircle size={18} />} color={testData.failed > 0 ? "#dc2626" : undefined} />
            <StatCard label={isZh ? "跳过" : "Skipped"} value={testData.skipped} icon={<AlertTriangle size={18} />} color="#c86f1d" />
            <StatCard
              label={isZh ? "通过率" : "Pass Rate"}
              value={`${passRate}%`}
              icon={<BarChart3 size={18} />}
              color={rateColor}
              large
            />
            <StatCard label={isZh ? "执行日期" : "Date"} value={testData.report_date} icon={<RefreshCw size={18} />} />
          </div>

          <div className="pass-bar-wrap">
            <span className="pass-bar-label">{isZh ? "通过率" : "Pass Rate"}</span>
            <div className="pass-bar-track">
              <div className="pass-bar-fill" style={{ width: `${passRate}%`, background: rateColor }} />
            </div>
            <span className="pass-bar-value" style={{ color: rateColor }}>{passRate}%</span>
          </div>
        </div>
      ) : null}

      {reportContent ? (
        <div className="report-preview">
          <div className="report-preview-header">
            <h3>{isZh ? "报告预览" : "Report Preview"}</h3>
          </div>
          <div className="report-preview-content">
            <MarkdownMessage content={reportContent} />
          </div>
        </div>
      ) : null}

      <style jsx>{`
        .testing-panel {
          min-height: 0;
          overflow: auto;
          padding: 22px;
          display: grid;
          align-content: start;
          gap: 20px;
        }
        .panel-header {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding-bottom: 16px;
          border-bottom: 1px solid var(--border);
        }
        .panel-header strong { display: block; font-size: 18px; margin-bottom: 4px; }
        .panel-subtitle { color: var(--muted); font-size: 13px; line-height: 1.5; }
        .action-bar { display: flex; gap: 10px; align-items: center; }
        .run-btn, .report-btn {
          display: inline-flex;
          align-items: center;
          gap: 7px;
          background: #167a72;
          color: #fff;
          border: 0;
          border-radius: 9px;
          padding: 10px 20px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: opacity 0.15s;
        }
        .report-btn { background: #5b4e9c; }
        .run-btn:hover:not(:disabled), .report-btn:hover:not(:disabled) { opacity: 0.88; }
        .run-btn:disabled, .report-btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .download-btn {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          border: 1px solid var(--border);
          border-radius: 8px;
          background: var(--panel);
          padding: 8px 16px;
          font-size: 13px;
          cursor: pointer;
          color: var(--text);
        }
        .download-btn:hover { background: #eef1f5; }
        .error-box {
          display: flex;
          align-items: center;
          gap: 8px;
          background: #fef2f2;
          border: 1px solid #fca5a5;
          border-radius: 8px;
          padding: 12px;
          color: #dc2626;
          font-size: 13px;
        }
        .test-summary { display: grid; gap: 16px; }
        .summary-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
          gap: 12px;
        }
        .stat-card {
          border: 1px solid var(--border);
          border-radius: 10px;
          background: var(--panel);
          padding: 14px;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .stat-card.large { grid-column: span 2; }
        .stat-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
        .stat-value { font-size: 24px; font-weight: 800; color: var(--text); line-height: 1; }
        .stat-icon { color: var(--muted); }
        .pass-bar-wrap { display: flex; align-items: center; gap: 10px; }
        .pass-bar-label { font-size: 13px; color: var(--muted); white-space: nowrap; width: 50px; }
        .pass-bar-track { flex: 1; height: 8px; background: var(--border); border-radius: 4px; overflow: hidden; }
        .pass-bar-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; }
        .pass-bar-value { font-size: 14px; font-weight: 700; width: 44px; text-align: right; }
        .report-preview {
          border: 1px solid var(--border);
          border-radius: 10px;
          background: var(--panel);
          overflow: hidden;
        }
        .report-preview-header { padding: 12px 16px; border-bottom: 1px solid var(--border); background: #fafbfc; }
        .report-preview-header h3 { margin: 0; font-size: 14px; color: var(--text); }
        .report-preview-content { padding: 16px; max-height: 520px; overflow: auto; }
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </section>
  );
}

function StatCard({
  label, value, icon, color, large,
}: {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color?: string;
  large?: boolean;
}) {
  return (
    <div className={`stat-card ${large ? "large" : ""}`}>
      <div className="stat-label">{label}</div>
      <div className="stat-icon">{icon}</div>
      <div className="stat-value" style={{ color: color || undefined }}>{value}</div>
    </div>
  );
}
