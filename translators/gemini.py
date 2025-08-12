from __future__ import annotations

from typing import Dict, Optional

import google.generativeai as genai

from .base import Translator


class GeminiTranslator(Translator):
    """Translator implementation using Google Gemini."""

    def __init__(self, api_key: str) -> None:
        super().__init__(api_key)
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel("gemini-pro")

    def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "ru",
        prompt: str = "",
        glossary: Optional[Dict[str, str]] = None,
    ) -> str:
        parts = []
        if glossary:
            glossary_text = "\n".join(f"{k} = {v}" for k, v in glossary.items())
            parts.append("Use the following glossary:\n" + glossary_text)
        if prompt:
            parts.append(prompt)
        parts.append(f"Translate from {source_lang} to {target_lang} the following text:\n{text}")
        final_prompt = "\n\n".join(parts)
        resp = self._model.generate_content(final_prompt)
        return resp.text.strip()
