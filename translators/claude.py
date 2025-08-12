from __future__ import annotations

from typing import Any

from .base import Translator


class ClaudeTranslator(Translator):
    """Stub for future Claude translator."""

    def translate(self, text: str, **ctx: Any) -> str:
        raise NotImplementedError("Claude translator is not implemented yet")
