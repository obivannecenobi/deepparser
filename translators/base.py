from __future__ import annotations

from abc import ABC, abstractmethod


class Translator(ABC):
    """Abstract base class for translation drivers."""

    def __init__(self, api_key: str | None = None, **kwargs):
        self.api_key = api_key or ""
        self._setup(**kwargs)

    def _setup(self, **kwargs) -> None:
        """Hook for subclasses to initialize API clients."""
        return

    @abstractmethod
    def translate(self, text: str, **ctx) -> str:
        """Translate *text* with optional context."""
        raise NotImplementedError
