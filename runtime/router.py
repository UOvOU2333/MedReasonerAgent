from __future__ import annotations

import os
from typing import Any

from tools.llm import call_llm
from tools.sglang_client import SGLangClient


class ModelRouter:
    def __init__(self) -> None:
        self.sglang = SGLangClient()

    def reason(self, prompt: str, engine: str | None = None) -> str:
        selected = engine or os.getenv("REASONING_ENGINE", "sglang")
        if selected == "sglang":
            return self.sglang.reason(prompt)
        return call_llm(prompt)

    def generate(self, prompt: str, metadata: dict[str, Any] | None = None) -> str:
        return call_llm(prompt, metadata=metadata)


router = ModelRouter()
