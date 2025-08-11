"""SQLite-backed storage for glossary entries with JSON import/export."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import GlossaryEntry


class GlossaryStore:
    """Store glossary entries in a SQLite database."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._init_db()

    # Database initialisation -------------------------------------------------
    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS terms(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_ru TEXT NOT NULL,
                match_mode TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                lock_inflection INTEGER DEFAULT 1,
                notes TEXT,
                tags TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS term_sources(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term_id INTEGER NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
                source_text TEXT NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()

    # Basic operations -------------------------------------------------------
    def add_entry(self, entry: GlossaryEntry, sources: Iterable[str]) -> int:
        """Insert a new glossary entry with sources and return its id."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO terms(target_ru,match_mode,priority,lock_inflection,notes,tags) VALUES(?,?,?,?,?,?)",
            (
                entry.target_ru,
                entry.match_mode,
                entry.priority,
                int(entry.lock_inflection),
                entry.notes,
                entry.tags,
            ),
        )
        entry_id = cur.lastrowid
        for s in sources:
            cur.execute(
                "INSERT INTO term_sources(term_id,source_text) VALUES(?,?)",
                (entry_id, s),
            )
        conn.commit()
        conn.close()
        return entry_id

    def get_entries(self) -> list[GlossaryEntry]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT id,target_ru,match_mode,priority,lock_inflection,notes,tags FROM terms ORDER BY id"
        )
        rows = cur.fetchall()
        conn.close()
        return [
            GlossaryEntry(
                id=r[0],
                target_ru=r[1],
                match_mode=r[2],
                priority=r[3],
                lock_inflection=bool(r[4]),
                notes=r[5] or "",
                tags=r[6] or "",
            )
            for r in rows
        ]

    def get_sources(self, entry_id: int) -> list[str]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT source_text FROM term_sources WHERE term_id=? ORDER BY id",
            (entry_id,),
        )
        rows = [r[0] for r in cur.fetchall()]
        conn.close()
        return rows

    # Context building -------------------------------------------------------
    def slice_for_context(self, project_id: int | None = None, limit: int = 50) -> list[dict]:
        """Return a slice of glossary entries suitable for translator context."""
        entries = self.get_entries()[:limit]
        result: list[dict] = []
        for e in entries:
            result.append(
                {
                    "target_ru": e.target_ru,
                    "match_mode": e.match_mode,
                    "sources": self.get_sources(e.id if e.id is not None else -1),
                }
            )
        return result

    # JSON import/export -----------------------------------------------------
    def export_json(self, path: Path) -> None:
        """Dump all entries to *path* in JSON format."""
        data = []
        for e in self.get_entries():
            data.append(
                {
                    "target_ru": e.target_ru,
                    "match_mode": e.match_mode,
                    "priority": e.priority,
                    "lock_inflection": e.lock_inflection,
                    "notes": e.notes,
                    "tags": e.tags,
                    "sources": self.get_sources(e.id if e.id is not None else -1),
                }
            )
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)

    def import_json(self, path: Path, *, replace: bool = False) -> None:
        """Import entries from JSON file at *path*.

        If *replace* is True existing entries are wiped before import.
        """
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        if replace:
            cur.execute("DELETE FROM term_sources")
            cur.execute("DELETE FROM terms")
        for item in data:
            cur.execute(
                "INSERT INTO terms(target_ru,match_mode,priority,lock_inflection,notes,tags) VALUES(?,?,?,?,?,?)",
                (
                    item.get("target_ru", ""),
                    item.get("match_mode", "exact"),
                    item.get("priority", 0),
                    int(item.get("lock_inflection", True)),
                    item.get("notes", ""),
                    item.get("tags", ""),
                ),
            )
            entry_id = cur.lastrowid
            for s in item.get("sources", []):
                cur.execute(
                    "INSERT INTO term_sources(term_id,source_text) VALUES(?,?)",
                    (entry_id, s),
                )
        conn.commit()
        conn.close()
