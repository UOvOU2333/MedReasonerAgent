from __future__ import annotations

import hashlib
import html
import os
from pathlib import Path

import fitz
import markdown

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENERATED_DIR = PROJECT_ROOT / "generated_docs"
RENDERED_DIR = GENERATED_DIR / "rendered"


def render_markdown_pdf(
    *,
    markdown_text: str | None = None,
    storage_path: str | None = None,
    output_name: str | None = None,
) -> dict:
    """Render Markdown content or a saved generated document to a PDF file."""
    if storage_path:
        source_path = resolve_generated_path(storage_path)
        markdown_text = source_path.read_text(encoding="utf-8")
        stem = source_path.stem
    elif markdown_text is not None:
        stem = output_name or "document"
    else:
        raise ValueError("markdown_text or storage_path is required")

    RENDERED_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(markdown_text.encode("utf-8")).hexdigest()[:10]
    safe_stem = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in stem)[:80]
    pdf_path = RENDERED_DIR / f"{safe_stem}_{digest}.pdf"

    html_body = markdown.markdown(
        markdown_text,
        extensions=["tables", "fenced_code", "sane_lists"],
        output_format="html5",
    )
    full_html = _wrap_html(html_body)

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    rect = fitz.Rect(36, 36, 559, 806)
    try:
        page.insert_htmlbox(rect, full_html)
    except Exception:
        page.insert_textbox(rect, _markdown_to_plain(markdown_text), fontsize=9, fontname="helv")
    doc.save(pdf_path)
    doc.close()

    rel_path = pdf_path.relative_to(PROJECT_ROOT).as_posix()
    return {
        "pdf_path": rel_path,
        "filename": pdf_path.name,
        "pdf_url": f"/docgen/rendered/{pdf_path.name}",
    }


def resolve_generated_path(storage_path: str) -> Path:
    raw = Path(storage_path.replace("\\", "/"))
    if raw.is_absolute():
        candidate = raw.resolve()
    else:
        candidate = (PROJECT_ROOT / raw).resolve()
    root = PROJECT_ROOT.resolve()
    if root not in candidate.parents and candidate != root:
        raise ValueError("storage_path must stay inside the project")
    if not candidate.exists() or not candidate.is_file():
        raise FileNotFoundError(storage_path)
    return candidate


def rendered_pdf_path(filename: str) -> Path:
    if filename != os.path.basename(filename) or not filename.endswith(".pdf"):
        raise ValueError("invalid PDF filename")
    path = (RENDERED_DIR / filename).resolve()
    if RENDERED_DIR.resolve() not in path.parents:
        raise ValueError("invalid PDF filename")
    return path


def _wrap_html(body: str) -> str:
    return f"""
<html>
<head>
<style>
body {{
  font-family: "Microsoft YaHei", "SimSun", sans-serif;
  font-size: 10px;
  line-height: 1.5;
  color: #17202a;
}}
h1 {{ font-size: 22px; margin: 0 0 12px; }}
h2 {{ font-size: 16px; margin: 18px 0 8px; border-bottom: 1px solid #d8dee8; padding-bottom: 4px; }}
h3 {{ font-size: 13px; margin: 14px 0 6px; }}
p {{ margin: 0 0 8px; }}
table {{ border-collapse: collapse; width: 100%; margin: 8px 0 12px; }}
th, td {{ border: 1px solid #cbd5e1; padding: 4px 6px; vertical-align: top; }}
th {{ background: #f1f5f9; }}
pre, code {{ font-family: Consolas, monospace; font-size: 8px; }}
pre {{ background: #f8fafc; border: 1px solid #d8dee8; padding: 6px; white-space: pre-wrap; }}
blockquote {{ border-left: 3px solid #cbd5e1; padding-left: 8px; color: #526070; }}
</style>
</head>
<body>{body}</body>
</html>
"""


def _markdown_to_plain(markdown_text: str) -> str:
    return html.unescape(markdown_text.replace("```", ""))
