from __future__ import annotations

from typing import Any

from .base import Translator


class GrokTranslator(Translator):
    """Stub for future Grok translator."""

    def translate(self, text: str, **ctx: Any) -> str:
        raise NotImplementedError("Grok translator is not implemented yet")
