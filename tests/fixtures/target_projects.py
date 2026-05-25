from __future__ import annotations

from pathlib import Path


def empty_project(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / "README.md").write_text("# Fixture Project\n", encoding="utf-8")
    return path
