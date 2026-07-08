from __future__ import annotations

from pathlib import Path
from typing import Any

from verifysignal_spec.workspace.product_context import load_product_context, summarize_safe_inspection


DEFAULT_CANDIDATES = ["README.md", "pyproject.toml", "package.json", "src/", "app/", "tests/", "docs/"]


def collect_safe_repository_context(project: Path, candidate_paths: list[str] | None = None) -> dict[str, Any]:
    candidates = candidate_paths or DEFAULT_CANDIDATES
    summary = summarize_safe_inspection(project, candidates)
    files: list[dict[str, str]] = []
    for rel_path in summary["safeInspectionPaths"]:
        path = project / rel_path
        if path.is_file():
            files.append({"path": rel_path, "kind": "file"})
        elif path.is_dir():
            files.append({"path": rel_path, "kind": "directory"})
    return {
        "productContext": load_product_context(project),
        "safeInspectionPaths": summary["safeInspectionPaths"],
        "blockedSensitivePaths": summary["blockedSensitivePaths"],
        "inspected": files,
    }

