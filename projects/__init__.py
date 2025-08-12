from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import json
import shutil


def ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


@dataclass
class Project:
    """Represents a single project stored on disk."""
    path: Path
    name: str
    status: str = "active"  # active or completed
    completed: bool = False
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def create(cls, base_dir: Path, name: str) -> "Project":
        path = ensure_dir(base_dir / name)
        ensure_dir(path / "Original")
        ensure_dir(path / "Translated")
        now = datetime.utcnow().isoformat()
        proj = cls(path=path, name=name, status="active", completed=False,
                   created_at=now, updated_at=now)
        proj.save()
        return proj

    @classmethod
    def load(cls, path: Path) -> "Project":
        with open(path / "project.json", "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return cls(path=path,
                   name=data.get("name", path.name),
                   status=data.get("status", "active"),
                   completed=data.get("completed", False),
                   created_at=data.get("created_at", ""),
                   updated_at=data.get("updated_at", ""))

    def save(self) -> None:
        self.completed = self.status == "completed"
        ensure_dir(self.path)
        ensure_dir(self.path / "Original")
        ensure_dir(self.path / "Translated")
        self.updated_at = datetime.utcnow().isoformat()
        data = {
            "name": self.name,
            "status": self.status,
            "completed": self.completed,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        with open(self.path / "project.json", "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)

    def mark_completed(self) -> None:
        self.status = "completed"
        self.save()

    def delete(self) -> None:
        if self.path.exists():
            shutil.rmtree(self.path)


class Archive:
    """Manage projects stored under a directory."""

    def __init__(self, workdir: Path):
        self.workdir = ensure_dir(workdir)

    def list(self, status: str = "active") -> list[Project]:
        result: list[Project] = []
        for entry in self.workdir.iterdir():
            pj = entry / "project.json"
            if entry.is_dir() and pj.exists():
                proj = Project.load(entry)
                if proj.status == status:
                    result.append(proj)
        return result

    def create(self, name: str) -> Project:
        return Project.create(self.workdir, name)

    def mark_completed(self, project: Project) -> None:
        project.mark_completed()

    def delete(self, project: Project) -> None:
        project.delete()
