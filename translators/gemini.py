from __future__ import annotations

import os
from typing import Any

from .base import Translator


class GeminiTranslator(Translator):
    """Translator implementation using Google Gemini API."""

    def _setup(self, model: str = "gemini-pro", **kwargs) -> None:
        import google.generativeai as genai

        key = self.api_key or os.getenv("GEMINI_API_KEY", "")
        genai.configure(api_key=key)
        self._model = genai.GenerativeModel(model)

    def translate(self, text: str, **ctx: Any) -> str:
        prompt = ctx.get("prompt", "Translate to Russian:")
        response = self._model.generate_content(f"{prompt}\n\n{text}")
        return getattr(response, "text", str(response))
