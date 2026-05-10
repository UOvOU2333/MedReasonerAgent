from __future__ import annotations

import os
from typing import Any

from openai import OpenAI


def call_llm(prompt: str, metadata: dict[str, Any] | None = None) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        return offline_response(prompt, metadata=metadata)

    client = OpenAI()
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""


def offline_response(prompt: str, metadata: dict[str, Any] | None = None) -> str:
    text = " ".join(prompt.strip().split())
    if "Extract biomedical entities" in text:
        terms = [
            word.strip(".,:;()[]").lower()
            for word in text.split()
            if len(word.strip(".,:;()[]")) > 4
        ]
        return ", ".join(dict.fromkeys(terms[:6])) or "symptom, disease"
    if "Decide workflow" in text:
        return "deep-reasoning"
    if "structured medical understanding" in text:
        return (
            '{"possible_disease":"requires clinical confirmation",'
            '"symptoms":["extracted from query"],'
            '"risk_factors":["unknown"],'
            '"clinical_interpretation":"Preliminary AI-assisted case summary.",'
            '"severity_estimation":"undetermined"}'
        )
    if "Explain the biomedical reasoning" in text:
        return (
            "The system extracted query entities, retrieved the closest DRG graph context, "
            "ranked plausible medical reasoning paths, and generated a guarded treatment summary."
        )
    if "treatment" in text.lower():
        return (
            '{"options":["confirm diagnosis with licensed clinician",'
            '"symptom-directed management"],'
            '"drug_candidates":[],"confidence":"low",'
            '"warnings":["Educational output only; not medical advice."]}'
        )
    if "reasoning" in text.lower():
        return "Query entities -> DRG concepts -> plausible mechanism -> clinical hypothesis."
    return "Preliminary medical reasoning generated from available query and graph context."
