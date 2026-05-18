"use client";

import { Bot, Send, UserRound } from "lucide-react";
import type { FormEvent } from "react";
import MarkdownMessage from "./MarkdownMessage";
import { useTraceStore } from "../store/traceStore";

type Props = {
  query: string;
  running: boolean;
  language: "zh" | "en";
  onQueryChange: (value: string) => void;
  onLanguageChange: (value: "zh" | "en") => void;
  onSubmit: (event: FormEvent) => void;
};

export default function ConversationPanel({ query, running, language, onQueryChange, onLanguageChange, onSubmit }: Props) {
  const messages = useTraceStore((state) => state.messages);
  const isZh = language === "zh";

  return (
    <section className="conversation">
      <div className="message-list">
        {messages.length === 0 ? (
          <div className="empty-state">
            <Bot size={22} />
            <strong>{isZh ? "医疗多 Agent 工作区" : "Medical multi-agent workspace"}</strong>
            <span>
              {isZh
                ? "输入医疗推理问题后，你会看到面向用户的解释；Agent 间传递的内部上下文会折叠在详情中。"
                : "Ask a clinical reasoning question. User-facing explanations stay visible, while internal agent context is folded into details."}
            </span>
          </div>
        ) : (
          messages.map((message) => (
            <article className={`message ${message.role}`} key={message.id}>
              <div className="message-icon">{message.role === "user" ? <UserRound size={16} /> : <Bot size={16} />}</div>
              <div className="message-body">
                <div className="message-title">{message.title}</div>
                <MarkdownMessage content={message.content} />
                {message.details ? (
                  <details>
                    <summary>{isZh ? "查看 Agent 内部传递内容" : "View internal agent handoff"}</summary>
                    <pre>{message.details}</pre>
                  </details>
                ) : null}
              </div>
            </article>
          ))
        )}
      </div>
      <form className="composer" onSubmit={onSubmit}>
        <div className="composer-tools">
          <label>
            {isZh ? "Agent 语言" : "Agent language"}
            <select value={language} onChange={(event) => onLanguageChange(event.target.value as "zh" | "en")}>
              <option value="zh">中文</option>
              <option value="en">English</option>
            </select>
          </label>
        </div>
        <textarea value={query} onChange={(event) => onQueryChange(event.target.value)} rows={3} />
        <button type="submit" disabled={running || !query.trim()} title={isZh ? "开始推理" : "Run reasoning"}>
          <Send size={17} />
        </button>
      </form>
      <style jsx>{`
        .conversation {
          min-height: 0;
          display: grid;
          grid-template-rows: 1fr auto;
          background: var(--bg);
        }
        .message-list {
          min-height: 0;
          overflow: auto;
          padding: 22px;
          display: grid;
          align-content: start;
          gap: 14px;
        }
        .empty-state {
          align-self: center;
          justify-self: center;
          width: min(520px, 100%);
          display: grid;
          gap: 8px;
          color: var(--muted);
          text-align: center;
          line-height: 1.5;
        }
        .empty-state strong {
          color: var(--text);
          font-size: 18px;
        }
        .message {
          display: grid;
          grid-template-columns: 30px minmax(0, 1fr);
          gap: 10px;
          max-width: 920px;
        }
        .message.user {
          justify-self: end;
          grid-template-columns: minmax(0, 1fr) 30px;
        }
        .message.user .message-icon {
          grid-column: 2;
          grid-row: 1;
          background: var(--accent);
          color: #fff;
        }
        .message.user .message-body {
          grid-column: 1;
          grid-row: 1;
          background: #e8f4f2;
          border-color: #badbd6;
        }
        .message-icon {
          width: 30px;
          height: 30px;
          display: grid;
          place-items: center;
          border-radius: 50%;
          background: #eef1f5;
          color: var(--muted);
        }
        .message-body {
          min-width: 0;
          border: 1px solid var(--border);
          border-radius: 8px;
          background: var(--panel);
          padding: 12px;
        }
        .message-title {
          margin-bottom: 8px;
          color: var(--muted);
          font-size: 12px;
          font-weight: 700;
        }
        pre {
          margin: 0;
          white-space: pre-wrap;
          word-break: break-word;
          line-height: 1.55;
          font-size: 13px;
          font-family: inherit;
        }
        details {
          margin-top: 10px;
          border-top: 1px solid var(--border);
          padding-top: 8px;
        }
        summary {
          cursor: pointer;
          color: var(--muted);
          font-size: 12px;
          font-weight: 700;
        }
        details pre {
          margin-top: 8px;
          color: var(--muted);
          font-size: 12px;
        }
        .composer {
          display: grid;
          grid-template-columns: minmax(0, 1fr) 44px;
          gap: 10px;
          padding: 14px;
          border-top: 1px solid var(--border);
          background: var(--panel);
        }
        .composer-tools {
          grid-column: 1 / -1;
          display: flex;
          justify-content: flex-end;
        }
        label {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          color: var(--muted);
          font-size: 12px;
          font-weight: 700;
        }
        select {
          height: 30px;
          border: 1px solid var(--border);
          border-radius: 6px;
          background: #fff;
          padding: 0 8px;
        }
        textarea {
          min-width: 0;
          resize: vertical;
          max-height: 180px;
          border: 1px solid var(--border);
          border-radius: 8px;
          padding: 10px 12px;
          line-height: 1.45;
        }
        button {
          width: 44px;
          height: 44px;
          border: 0;
          border-radius: 8px;
          display: grid;
          place-items: center;
          background: var(--accent);
          color: #fff;
          cursor: pointer;
        }
        button:disabled {
          opacity: 0.55;
          cursor: not-allowed;
        }
      `}</style>
    </section>
  );
}
