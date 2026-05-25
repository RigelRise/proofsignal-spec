from __future__ import annotations

import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from proofsignal_spec.workspace.product_context import load_product_context, save_product_context
from proofsignal_spec.workspace.repository import init_workspace, now_iso
from proofsignal_spec.workflows.stage_documents import write_global_understanding

from .target_workspace import write_basic_target


def create_missing_understanding_workspace(project: Path) -> Path:
    write_basic_target(project)
    return project


def create_current_understanding_workspace(project: Path, candidates: list[dict[str, Any]] | None = None) -> Path:
    write_basic_target(project)
    init_workspace(project)
    context = load_product_context(project)
    context["repositorySummary"] = "Test App is a small browser application."
    context["safeInspectionPaths"] = ["README.md", "src/"]
    context["blockedSensitivePaths"] = [".env"]
    context["understanding"] = {
        "generatedAt": now_iso(),
        "generatedGitHash": None,
        "gitAvailable": False,
        "staleReasons": [],
    }
    context["candidateUseCases"] = candidates or [sample_candidate()]
    save_product_context(project, context)
    write_global_understanding(project, context)
    return project


def create_stale_understanding_workspace(project: Path) -> Path:
    create_current_understanding_workspace(project)
    context = load_product_context(project)
    context["understanding"]["generatedAt"] = (
        datetime.now(UTC).replace(microsecond=0) - timedelta(days=8)
    ).isoformat().replace("+00:00", "Z")
    save_product_context(project, context)
    write_global_understanding(project, context)
    return project


def sample_candidate(alias: str = "login") -> dict[str, Any]:
    return {
        "candidateAlias": alias,
        "title": "Validate user login",
        "behavior": "User signs in with a QA account.",
        "targetSurface": "Login page",
        "expectedOutcome": "Dashboard is visible.",
        "rationale": "Authentication is a high-value browser flow.",
        "sourceContext": ["README.md"],
        "confidence": "medium",
    }


def create_git_workspace_with_stale_commit(project: Path, commit_count: int = 11) -> tuple[Path, str]:
    write_basic_target(project)
    subprocess.run(["git", "init"], cwd=project, check=True, capture_output=True)
    subprocess.run(["git", "add", "README.md", "src/app.py"], cwd=project, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=qa@example.com", "-c", "user.name=QA", "commit", "-m", "initial"],
        cwd=project,
        check=True,
        capture_output=True,
    )
    generated_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=project, text=True).strip()
    for index in range(commit_count):
        path = project / "src" / f"change_{index}.txt"
        path.write_text(f"change {index}\n", encoding="utf-8")
        subprocess.run(["git", "add", str(path.relative_to(project))], cwd=project, check=True, capture_output=True)
        subprocess.run(
            ["git", "-c", "user.email=qa@example.com", "-c", "user.name=QA", "commit", "-m", f"change {index}"],
            cwd=project,
            check=True,
            capture_output=True,
        )
    init_workspace(project)
    context = load_product_context(project)
    context["repositorySummary"] = "Git-backed test app."
    context["understanding"] = {
        "generatedAt": now_iso(),
        "generatedGitHash": generated_hash,
        "gitAvailable": True,
        "staleReasons": [],
    }
    context["candidateUseCases"] = [sample_candidate()]
    save_product_context(project, context)
    write_global_understanding(project, context)
    return project, generated_hash
