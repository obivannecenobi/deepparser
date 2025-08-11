'''Build context dictionaries for translator requests.'''
from __future__ import annotations

from typing import Any


class DummyProjectMemory:
    """Minimal project memory placeholder."""

    def context_for(self, chapter_id: int) -> dict:
        return {}


class ContextBuilder:
    """Combine glossary slice, project memory and mini‑prompt."""

    def __init__(self, glossary_store, project_memory: Any | None = None, settings: Any | None = None):
        self.glossary_store = glossary_store
        self.project_memory = project_memory or DummyProjectMemory()
        # settings expected to have `glossary_max` and `format_policy`
        self.settings = settings or type("S", (), {"glossary_max": 50, "format_policy": ""})()

    def build(self, project_id: int, chapter_id: int, miniprompt: str) -> dict:
        """Return context dict for translator."""
        gl_slice = self.glossary_store.slice_for_context(project_id, limit=self.settings.glossary_max)
        pm = self.project_memory.context_for(chapter_id)
        return {
            "glossary": gl_slice,
            "project_memory": pm,
            "miniprompt": miniprompt,
            "format_policy": getattr(self.settings, "format_policy", ""),
        }
