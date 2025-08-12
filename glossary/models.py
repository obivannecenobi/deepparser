"""Data models for glossary entries."""
from dataclasses import dataclass


@dataclass
class GlossaryEntry:
    id: int | None
    target_ru: str
    match_mode: str  # exact|normalized|regex|fuzzy
    priority: int = 0
    lock_inflection: bool = True
    notes: str = ""
    tags: str = ""


@dataclass
class TermSource:
    id: int | None
    entry_id: int
    source_text: str
