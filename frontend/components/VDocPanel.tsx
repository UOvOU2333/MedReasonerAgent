"use client";

import { Database, FileArchive, HardDrive, Shield } from "lucide-react";

export default function VDocPanel() {
  return (
    <section className="vdoc-panel">
      <div className="vdoc-center">
        <div className="vdoc-logo">
          <div className="vdoc-logo-ring">
            <Database size={48} />
          </div>
          <div className="vdoc-orbits">
            <div className="vdoc-orbit orbit-1"><FileArchive size={16} /></div>
            <div className="vdoc-orbit orbit-2"><HardDrive size={16} /></div>
            <div className="vdoc-orbit orbit-3"><Shield size={16} /></div>
          </div>
        </div>
        <h2>虚拟文档系统智能体</h2>
        <p className="vdoc-desc">
          虚拟文档系统是文档存储的中间层服务。
          <br />
          它接收其他智能体（如文档自动生成智能体）生成的文档，
          <br />
          经过格式验证、元数据标记后，安全存储到项目文件系统中。
        </p>
        <div className="vdoc-features">
          <div className="vdoc-feature">
            <span className="vdoc-feature-icon">📥</span>
            <strong>文档接收</strong>
            <small>从上游智能体接收待存储文档</small>
          </div>
          <div className="vdoc-feature">
            <span className="vdoc-feature-icon">✅</span>
            <strong>格式验证</strong>
            <small>检查文档格式规范与完整性</small>
          </div>
          <div className="vdoc-feature">
            <span className="vdoc-feature-icon">🏷️</span>
            <strong>元数据标记</strong>
            <small>自动添加版本、日期等标签</small>
          </div>
          <div className="vdoc-feature">
            <span className="vdoc-feature-icon">💾</span>
            <strong>安全存储</strong>
            <small>保存到 generated_docs/ 目录</small>
          </div>
          <div className="vdoc-feature">
            <span className="vdoc-feature-icon">📋</span>
            <strong>索引维护</strong>
            <small>自动更新文档索引文件</small>
          </div>
        </div>

        <div className="vdoc-pipeline">
          <span className="pipeline-label">子智能体流水线</span>
          <div className="pipeline-flow">
            <div className="pipeline-node">📨 Receiver</div>
            <span className="pipeline-arrow">→</span>
            <div className="pipeline-node">🔍 Validator</div>
            <span className="pipeline-arrow">→</span>
            <div className="pipeline-node">🏷️ Tagger</div>
            <span className="pipeline-arrow">→</span>
            <div className="pipeline-node">💾 Storer</div>
            <span className="pipeline-arrow">→</span>
            <div className="pipeline-node">📢 Notifier</div>
          </div>
        </div>

        <div className="vdoc-status">
          <div className="vdoc-status-dot" />
          <span>系统就绪 — 等待文档生成任务</span>
        </div>
      </div>

      <style jsx>{`
        .vdoc-panel {
          min-height: 0;
          overflow: auto;
          padding: 40px 22px;
          display: grid;
          place-items: center;
        }
        .vdoc-center {
          max-width: 560px;
          text-align: center;
          display: grid;
          gap: 24px;
          justify-items: center;
        }
        .vdoc-logo {
          position: relative;
          width: 120px;
          height: 120px;
          display: grid;
          place-items: center;
        }
        .vdoc-logo-ring {
          width: 90px;
          height: 90px;
          display: grid;
          place-items: center;
          border-radius: 50%;
          border: 3px solid var(--border);
          background: var(--panel);
          color: var(--accent);
          z-index: 1;
        }
        .vdoc-orbits {
          position: absolute;
          inset: 0;
        }
        .vdoc-orbit {
          position: absolute;
          width: 30px;
          height: 30px;
          display: grid;
          place-items: center;
          border-radius: 50%;
          background: var(--panel);
          border: 1px solid var(--border);
          color: var(--muted);
        }
        .orbit-1 { top: 0; left: 50%; margin-left: -15px; }
        .orbit-2 { top: 50%; right: -4px; margin-top: -15px; }
        .orbit-3 { bottom: 0; left: 50%; margin-left: -15px; }
        .vdoc-panel h2 {
          margin: 0;
          font-size: 22px;
          color: var(--text);
        }
        .vdoc-desc {
          margin: 0;
          color: var(--muted);
          font-size: 14px;
          line-height: 1.7;
        }
        .vdoc-features {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
          gap: 12px;
          width: 100%;
        }
        .vdoc-feature {
          display: grid;
          gap: 4px;
          justify-items: center;
          border: 1px solid var(--border);
          border-radius: 10px;
          background: var(--panel);
          padding: 14px 10px;
        }
        .vdoc-feature-icon {
          font-size: 22px;
        }
        .vdoc-feature strong {
          font-size: 13px;
          color: var(--text);
        }
        .vdoc-feature small {
          font-size: 11px;
          color: var(--muted);
          line-height: 1.3;
        }
        .vdoc-pipeline {
          border: 1px solid var(--border);
          border-radius: 10px;
          background: var(--panel);
          padding: 14px 18px;
          width: 100%;
        }
        .pipeline-label {
          display: block;
          font-size: 11px;
          font-weight: 700;
          color: var(--muted);
          margin-bottom: 10px;
          text-transform: uppercase;
        }
        .pipeline-flow {
          display: flex;
          align-items: center;
          justify-content: center;
          flex-wrap: wrap;
          gap: 4px;
          font-size: 12px;
          font-weight: 600;
        }
        .pipeline-node {
          border: 1px solid var(--border);
          border-radius: 6px;
          background: #f8fafc;
          padding: 4px 10px;
          white-space: nowrap;
        }
        .pipeline-arrow {
          color: var(--muted);
          font-size: 14px;
          margin: 0 2px;
        }
        .vdoc-status {
          display: flex;
          align-items: center;
          gap: 8px;
          color: var(--ok);
          font-size: 13px;
          font-weight: 600;
        }
        .vdoc-status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--ok);
        }
      `}</style>
    </section>
  );
}
