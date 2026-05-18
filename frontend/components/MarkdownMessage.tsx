"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function MarkdownMessage({ content }: { content: string }) {
  return (
    <div className="markdown-message">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
      <style jsx global>{`
        .markdown-message {
          font-size: 13px;
          line-height: 1.58;
        }
        .markdown-message > :first-child {
          margin-top: 0;
        }
        .markdown-message > :last-child {
          margin-bottom: 0;
        }
        .markdown-message p,
        .markdown-message ul,
        .markdown-message ol,
        .markdown-message blockquote,
        .markdown-message table {
          margin: 0 0 10px;
        }
        .markdown-message ul,
        .markdown-message ol {
          padding-left: 18px;
        }
        .markdown-message li {
          margin: 3px 0;
        }
        .markdown-message code {
          border: 1px solid var(--border);
          border-radius: 4px;
          background: #f6f8fb;
          padding: 1px 4px;
          font-size: 12px;
        }
        .markdown-message pre {
          overflow: auto;
          border: 1px solid var(--border);
          border-radius: 6px;
          background: #f6f8fb;
          padding: 10px;
        }
        .markdown-message pre code {
          border: 0;
          background: transparent;
          padding: 0;
        }
        .markdown-message table {
          width: 100%;
          border-collapse: collapse;
          font-size: 12px;
        }
        .markdown-message th,
        .markdown-message td {
          border: 1px solid var(--border);
          padding: 6px;
          text-align: left;
        }
        .markdown-message blockquote {
          border-left: 3px solid var(--border);
          padding-left: 10px;
          color: var(--muted);
        }
      `}</style>
    </div>
  );
}
