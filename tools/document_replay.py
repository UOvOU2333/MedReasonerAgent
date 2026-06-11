from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


JSON_BLOCK = re.compile(r"```json\s*(.*?)```", re.DOTALL | re.IGNORECASE)


@dataclass
class ExtractedCase:
    index: int
    raw: str
    emr: dict[str, Any] | None
    expected: dict[str, Any]
    error: str


def extract_json_cases(markdown_text: str) -> list[ExtractedCase]:
    cases: list[ExtractedCase] = []
    for index, match in enumerate(JSON_BLOCK.finditer(markdown_text), start=1):
        raw = match.group(1).strip()
        value, error = _loads_json_block(raw)
        if error:
            cases.append(ExtractedCase(index, raw, None, {}, error))
            continue
        if not isinstance(value, dict):
            cases.append(ExtractedCase(index, raw, None, {}, "JSON block is not an object"))
            continue
        expected = _extract_expected(value)
        emr = {k: v for k, v in value.items() if k not in {"expected", "result"}}
        cases.append(ExtractedCase(index, raw, emr, expected, ""))
    return cases


def compare_drg_result(actual: dict[str, Any], expected: dict[str, Any]) -> tuple[bool, str]:
    if expected:
        mismatches = []
        for key in ("mdc", "adrg", "drg", "complication"):
            if key in expected and str(actual.get(key, "")).lower() != str(expected.get(key, "")).lower():
                mismatches.append(f"{key}: expected {expected.get(key)}, got {actual.get(key)}")
        return len(mismatches) == 0, "; ".join(mismatches)
    drg = actual.get("drg")
    ok = bool(drg and drg != "N/A")
    return ok, "" if ok else "No expected result; actual DRG grouping failed"


def _loads_json_block(raw: str) -> tuple[Any, str]:
    candidates = [raw]
    if "{{" in raw or "}}" in raw:
        candidates.append(raw.replace("{{", "{").replace("}}", "}"))
    last_error = ""
    for candidate in candidates:
        try:
            return json.loads(candidate), ""
        except json.JSONDecodeError as exc:
            last_error = f"JSON parse error: {exc.msg}"
    return None, last_error


def _extract_expected(value: dict[str, Any]) -> dict[str, Any]:
    raw = value.get("expected") or value.get("result") or {}
    if not isinstance(raw, dict):
        return {}
    return {key: raw[key] for key in ("mdc", "adrg", "drg", "complication") if key in raw}
