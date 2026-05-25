from __future__ import annotations

import re
from pathlib import Path

WORKSPACE_DIR = ".proofsignal"
WORKSPACE_FILE = "workspace.yaml"
PRODUCT_CONTEXT_FILE = "product-context.yaml"
REGISTRY_FILE = "registry.yaml"
USE_CASES_DIR = "use-cases"
RUN_REQUESTS_DIR = "run-requests"
SKILLS_DIR = "skills"
RUNS_DIR = "runs"
REPAIRS_DIR = "repairs"
INTEGRATIONS_DIR = "integrations"
MANIFESTS_DIR = "manifests"

ALIAS_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")


def resolve_project_path(project_path: str | None = None, here: bool = False) -> Path:
    if project_path and here:
        raise ValueError("Use either project path or --here, not both.")
    return Path(project_path or ".").resolve()


def workspace_root(project: Path) -> Path:
    return project / WORKSPACE_DIR


def registry_path(project: Path) -> Path:
    return workspace_root(project) / REGISTRY_FILE


def product_context_path(project: Path) -> Path:
    return workspace_root(project) / PRODUCT_CONTEXT_FILE


def use_case_path(project: Path, alias: str) -> Path:
    return workspace_root(project) / USE_CASES_DIR / f"{alias}.yaml"


def run_request_path(project: Path, alias: str) -> Path:
    return workspace_root(project) / RUN_REQUESTS_DIR / f"{alias}.yaml"


def skill_path(project: Path, name: str) -> Path:
    return workspace_root(project) / SKILLS_DIR / f"{name}.browser.md"


def repair_path(project: Path, repair_id: str) -> Path:
    return workspace_root(project) / REPAIRS_DIR / f"{repair_id}.yaml"


def run_history_path(project: Path, alias: str, run_id: str) -> Path:
    return workspace_root(project) / RUNS_DIR / alias / f"{run_id}.yaml"


def integration_state_path(project: Path) -> Path:
    return workspace_root(project) / INTEGRATIONS_DIR / "state.yaml"


def manifest_path(project: Path, integration_key: str) -> Path:
    return workspace_root(project) / INTEGRATIONS_DIR / MANIFESTS_DIR / f"{integration_key}.yaml"


def ensure_path_safe_alias(alias: str) -> str:
    if not ALIAS_RE.match(alias):
        raise ValueError("Alias must be lowercase path-safe text using letters, numbers, '.', '_' or '-'.")
    return alias


def to_project_relative(project: Path, path: Path) -> str:
    return path.resolve().relative_to(project.resolve()).as_posix()


def project_relative_path(project: Path, rel_path: str) -> Path:
    path = (project / rel_path).resolve()
    project_root = project.resolve()
    try:
        path.relative_to(project_root)
    except ValueError as exc:
        raise ValueError(f"Path escapes target project: {rel_path}") from exc
    return path


def workspace_dirs(project: Path) -> list[Path]:
    root = workspace_root(project)
    return [
        root,
        root / USE_CASES_DIR,
        root / RUN_REQUESTS_DIR,
        root / SKILLS_DIR,
        root / RUNS_DIR,
        root / REPAIRS_DIR,
        root / INTEGRATIONS_DIR,
        root / INTEGRATIONS_DIR / MANIFESTS_DIR,
    ]
