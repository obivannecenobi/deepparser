from __future__ import annotations

from typing import Any

from .base import Translator


class GPT5Translator(Translator):
    """Stub for future GPT-5 translator."""

    def translate(self, text: str, **ctx: Any) -> str:
        raise NotImplementedError("GPT-5 translator is not implemented yet")
