from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional


class Translator(ABC):
    """Base translator interface."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    @abstractmethod
    def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "ru",
        prompt: str = "",
        glossary: Optional[Dict[str, str]] = None,
    ) -> str:
        """Translate text and return result."""
        raise NotImplementedError
