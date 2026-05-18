from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def call_llm(prompt: str, metadata: dict[str, Any] | None = None) -> str:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return offline_response(prompt, metadata=metadata)

    client = OpenAI(api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL") or None)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    request: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    if model != "deepseek-reasoner":
        request["temperature"] = float(os.getenv("LLM_TEMPERATURE", "0.2"))

    resp = client.chat.completions.create(**request)
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
