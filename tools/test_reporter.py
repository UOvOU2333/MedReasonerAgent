"""Run pytest and collect structured results for LLM report generation."""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).parent.parent
REPORT_DATE = date.today().isoformat()


def run_pytest() -> dict[str, Any]:
    """
    Run pytest and parse its verbose output to build structured results.
    Raises RuntimeError if pytest is not available.
    """
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "--tb=short",
            "-v",
            "--color=no",
        ],
        cwd=str(_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = result.stdout + "\n" + result.stderr

    summary_matches = re.findall(
        r"(?:(\d+) failed)?,?\s*(?:(\d+) passed)?(?:, (\d+) xfailed)?(?:, (\d+) xpassed)?(?:, (\d+) skipped)?(?:, (\d+) error)?",
        output,
    )
    passed = 0
    xfailed = 0
    xpassed = 0
    skipped = 0
    failed = 0
    error = 0
    for m in summary_matches:
        if m[0] or m[1]:  # at least one count is non-zero
            # group order: failed, passed, xfailed, xpassed, skipped, error
            failed = int(m[0] or 0)
            passed = int(m[1] or 0)
            xfailed = int(m[2] or 0)
            xpassed = int(m[3] or 0)
            skipped = int(m[4] or 0)
            error = int(m[5] or 0)
            break  # use the first substantive match

    total = passed + xfailed + xpassed + skipped + failed + error

    # Parse individual test lines: test_file.py::TestClass::test_name PASSED/FAILED/etc
    test_lines: list[dict[str, str]] = []
    for line in output.splitlines():
        m = re.match(
            r"(.+?)::(.+?)::(.+?)\s+(PASSED|FAILED|SKIPPED|XFAILED|XPASSED|ERROR)",
            line,
        )
        if m:
            test_lines.append({
                "file": m.group(1),
                "classname": m.group(2),
                "name": m.group(3),
                "status": m.group(4),
            })

    # Build by-file aggregation
    by_file: dict[str, dict[str, Any]] = {}
    for t in test_lines:
        fn = t["file"]
        if fn not in by_file:
            by_file[fn] = {
                "file": fn,
                "tests": [],
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "error": 0,
            }
        by_file[fn]["tests"].append({
            "classname": t["classname"],
            "name": t["name"],
            "status": t["status"],
        })
        key = t["status"].lower()
        if key in by_file[fn]:
            by_file[fn][key] += 1

    # Extract failure messages
    # pytest summary format: FAILED tests/test_agents/test_file.py::TestClass::test_name - assert False
    failed_tests: list[dict[str, str]] = []
    for line in output.splitlines():
        if line.startswith("FAILED "):
            rest = line[len("FAILED "):]
            test_id = rest.split(" - ")[0].strip()
            msg = " | ".join(rest.split(" - ")[1:])[:300] if " - " in rest else ""
            file_name = test_id.split("::")[0] if "::" in test_id else test_id
            if not any(ft["test_id"] == test_id for ft in failed_tests):
                failed_tests.append({"test_id": test_id, "message": msg, "file": file_name})

    return {
        "report_date": REPORT_DATE,
        "total": total,
        "passed": passed,
        "xfailed": xfailed,
        "xpassed": xpassed,
        "skipped": skipped,
        "failed": failed,
        "error": error,
        "pass_rate": round(passed / total * 100, 1) if total > 0 else 0.0,
        "by_file": list(by_file.values()),
        "failed_tests": failed_tests,
        "output_snippet": output[-4000:],
        "exit_code": result.returncode,
    }


def build_test_report_prompt(test_data: dict[str, Any], language: str = "zh") -> str:
    """Build a prompt for LLM to generate a test report from pytest results."""
    is_zh = language == "zh"
    summary_lines = [
        f"## 测试执行摘要",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 执行日期 | {test_data.get('report_date', '')} |",
        f"| 用例总数 | {test_data.get('total', 0)} |",
        f"| 通过数 | {test_data.get('passed', 0)} |",
        f"| 失败数 | {test_data.get('failed', 0)} |",
        f"| 跳过数 | {test_data.get('skipped', 0)} |",
        f"| 预期失败(XFAIL) | {test_data.get('xfailed', 0)} |",
        f"| 预期失败但通过(XPASS) | {test_data.get('xpassed', 0)} |",
        f"| 错误数 | {test_data.get('error', 0)} |",
        f"| 通过率 | {test_data.get('pass_rate', 0.0)}% |",
    ]
    summary_md = "\n".join(summary_lines)

    file_lines = ["\n## 按文件汇总\n"]
    for f in test_data.get("by_file", []):
        total_f = f.get("passed", 0) + f.get("failed", 0) + f.get("skipped", 0) + f.get("error", 0)
        pass_f = f.get("passed", 0)
        rate_f = round(pass_f / total_f * 100, 1) if total_f > 0 else 0.0
        file_lines.append(f"### {f['file']}")
        file_lines.append(f"| 指标 | 值 |")
        file_lines.append(f"|------|---|")
        file_lines.append(f"| 通过 | {f.get('passed', 0)} |")
        file_lines.append(f"| 失败 | {f.get('failed', 0)} |")
        file_lines.append(f"| 跳过 | {f.get('skipped', 0)} |")
        file_lines.append(f"| 通过率 | {rate_f}% |")
        file_lines.append("")

    failed_lines = ["\n## 失败测试详情\n"]
    for ft in test_data.get("failed_tests", []):
        failed_lines.append(f"- **{ft['test_id']}**")
        if ft.get("message"):
            msg = ft["message"].replace("\n", " ")[:200]
            failed_lines.append(f"  - 原因: {msg}")
        failed_lines.append("")

    return f"""You are a QA engineer generating a test execution report.

Project: MedReasonerAgent
Test execution date: {test_data.get('report_date', '')}
Language: {'Chinese' if is_zh else 'English'}

Generate a complete test execution report in {'Chinese' if is_zh else 'English'}.

CRITICAL — Use these EXACT markdown section headings (copy them verbatim):

## 1. 执行概述
## 2. 测试结果摘要
## 3. 按文件/模块分析
## 4. 失败测试分析
## 5. 覆盖率与质量评估
## 6. 改进建议

{summary_md}
{"".join(file_lines)}
{"".join(failed_lines)}

Format requirements:
- Include the meta information table at the top: | 属性 | 内容 | with 项目名称, 文档类型, 文档版本, 生成日期 ({REPORT_DATE}), 生成方式, 状态
- Use Markdown tables where appropriate
- For section ## 4, analyze each failed test and provide root-cause hypotheses
- For section ## 5, assess overall quality based on pass rate and failure patterns
- For section ## 6, give concrete actionable recommendations
- Document MUST end with: "*本文档由 DocGen Agent 自动生成，状态为草稿，需人工审核确认。*"
- NO "TODO", "TBD", "待定" or any placeholder text anywhere

Document title: # MedReasonerAgent 测试执行报告
"""


def build_testing_doc_content(
    test_doc: str,
    test_data: dict[str, Any],
    llm_report: str,
) -> str:
    """
    Merge the AI-generated test plan document, pytest execution data,
    and LLM analysis report into a single complete testing document.

    Structure:
    1. Cover / meta table
    2. Part I — Test Plan (AI-generated, static)
    3. Part II — Test Execution Data (live pytest results)
    4. Part III — Test Execution Report (LLM analysis)
    """
    is_zh = True
    # Detect language from the test plan content
    if "## 1. 执行概述" in test_doc or "执行日期" in test_doc:
        is_zh = True
    elif "## 1. Execution Overview" in test_doc:
        is_zh = False

    meta_label = "测试文档" if is_zh else "Testing Document"
    part1_label = "测试方案" if is_zh else "Test Plan"
    part2_label = "测试执行数据" if is_zh else "Test Execution Data"
    part3_label = "测试执行报告" if is_zh else "Test Execution Report"

    # Section 2 — pytest data
    td = test_data
    pass_rate = td.get("pass_rate", 0.0)
    rate_color = "✅" if pass_rate >= 80 else ("⚠️" if pass_rate >= 50 else "❌")
    exec_section = f"""## {part2_label}

### 2.1 执行摘要

| 属性 | 内容 |
|------|------|
| 执行日期 | {td.get('report_date', '')} |
| 用例总数 | {td.get('total', 0)} |
| 通过数 | {td.get('passed', 0)} |
| 失败数 | {td.get('failed', 0)} |
| 跳过数 | {td.get('skipped', 0)} |
| 预期失败(XFAIL) | {td.get('xfailed', 0)} |
| 预期失败但通过(XPASS) | {td.get('xpassed', 0)} |
| 错误数 | {td.get('error', 0)} |
| 通过率 | {pass_rate}% {rate_color} |

### 2.2 按文件汇总
"""

    for f in td.get("by_file", []):
        f_total = f.get("passed", 0) + f.get("failed", 0) + f.get("skipped", 0) + f.get("error", 0)
        f_pass = f.get("passed", 0)
        f_rate = round(f_pass / f_total * 100, 1) if f_total > 0 else 0.0
        exec_section += f"""
#### {f.get('file', 'unknown')}

| 指标 | 值 |
|------|---|
| 通过 | {f_pass} |
| 失败 | {f.get('failed', 0)} |
| 跳过 | {f.get('skipped', 0)} |
| 错误 | {f.get('error', 0)} |
| 通过率 | {f_rate}% |
"""

    if td.get("failed_tests"):
        exec_section += f"\n### 2.3 失败测试详情\n\n"
        for ft in td["failed_tests"]:
            exec_section += f"- **{ft.get('test_id', 'unknown')}**"
            if ft.get("message"):
                exec_section += f"\n  - 原因: {ft['message'].replace(chr(10), ' ')[:200]}"
            exec_section += "\n"

    # Section 3 — LLM report (strip the meta table that build_test_report_prompt prepends)
    # The LLM report already has its own section headings
    report_section = f"""## {part3_label}

{llm_report}
"""

    # Strip duplicate meta table from llm_report if present
    # (the prompt asks for a meta table, but we already output one above)
    report_section = report_section.strip()

    return f"""{test_doc}

---

{exec_section}

{report_section}

---

*本文档由 MedReasonerAgent DocGen Agent 自动生成，测试数据来自实时 pytest 执行，报告由 LLM 分析。状态：草稿，需人工审核确认。*
"""
