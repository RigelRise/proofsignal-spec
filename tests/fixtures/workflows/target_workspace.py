from __future__ import annotations

from pathlib import Path


def write_basic_target(project: Path) -> Path:
    project.mkdir(parents=True, exist_ok=True)
    (project / "README.md").write_text("# Test App\n\nA small browser application.\n", encoding="utf-8")
    (project / "src").mkdir(exist_ok=True)
    (project / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
    return project

