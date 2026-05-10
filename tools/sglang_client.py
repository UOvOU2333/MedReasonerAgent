from __future__ import annotations

import os

import httpx

from tools.llm import call_llm


class SGLangClient:
    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = base_url or os.getenv("SGLANG_BASE_URL")
        self.model = model or os.getenv("SGLANG_MODEL", "default")

    def reason(self, prompt: str) -> str:
        """
        Call SGLang if SGLANG_BASE_URL is configured; otherwise use the default LLM API.
        """
        if not self.base_url:
            return call_llm(prompt, metadata={"engine": "llm_fallback"})

        response = httpx.post(
            f"{self.base_url.rstrip('/')}/v1/chat/completions",
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
