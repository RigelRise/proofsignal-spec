from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import layout
from .models import ArtifactReference, RunHistoryEntry, UseCaseRecord


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_document(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return default
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return _load_simple_yaml(text)


def save_document(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(data, indent=2, sort_keys=False) + "\n"
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(serialized)
        Path(tmp).replace(path)
    finally:
        tmp_path = Path(tmp)
        if tmp_path.exists():
            tmp_path.unlink()


def _load_simple_yaml(text: str) -> Any:
    """Parse a small YAML subset used by old/manual workspace files.

    JSON is the writer format because JSON is valid YAML. This reader only
    handles simple key/value and one-level list files to keep the CLI usable
    without PyYAML in minimal environments.
    """
    result: dict[str, Any] = {}
    current_key: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") and current_key:
            result.setdefault(current_key, []).append(_parse_scalar(line[4:]))
            continue
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            current_key = key.strip()
            value = value.strip()
            if value == "":
                result[current_key] = []
            elif value.startswith("[") and value.endswith("]"):
                items = [item.strip() for item in value[1:-1].split(",") if item.strip()]
                result[current_key] = [_parse_scalar(item) for item in items]
            else:
                result[current_key] = _parse_scalar(value)
    return result


def _parse_scalar(value: str) -> Any:
    value = value.strip().strip('"').strip("'")
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.lower() in {"null", "none"}:
        return None
    try:
        return int(value)
    except ValueError:
        return value


def init_workspace(project: Path, force: bool = False, core_cmd: str | None = None) -> dict[str, Any]:
    root = layout.workspace_root(project)
    for directory in layout.workspace_dirs(project):
        directory.mkdir(parents=True, exist_ok=True)

    created = now_iso()
    workspace = load_document(root / layout.WORKSPACE_FILE, default={}) or {}
    workspace.setdefault("workspaceVersion", "proofsignal-spec-workspace/v1")
    workspace.setdefault("createdAt", created)
    workspace["updatedAt"] = now_iso()
    workspace.update(
        {
            "productContextPath": f"{layout.WORKSPACE_DIR}/{layout.PRODUCT_CONTEXT_FILE}",
            "registryPath": f"{layout.WORKSPACE_DIR}/{layout.REGISTRY_FILE}",
            "useCasesDir": f"{layout.WORKSPACE_DIR}/{layout.USE_CASES_DIR}",
            "runRequestsDir": f"{layout.WORKSPACE_DIR}/{layout.RUN_REQUESTS_DIR}",
            "skillsDir": f"{layout.WORKSPACE_DIR}/{layout.SKILLS_DIR}",
            "runsDir": f"{layout.WORKSPACE_DIR}/{layout.RUNS_DIR}",
            "repairsDir": f"{layout.WORKSPACE_DIR}/{layout.REPAIRS_DIR}",
            "integrationsDir": f"{layout.WORKSPACE_DIR}/{layout.INTEGRATIONS_DIR}",
        }
    )
    if core_cmd:
        workspace["coreCommand"] = core_cmd
    save_document(root / layout.WORKSPACE_FILE, workspace)

    product_context_path = layout.product_context_path(project)
    if force or not product_context_path.exists():
        product_context = {
            "schemaVersion": "proofsignal-spec-product-context/v1",
            "productName": project.name,
            "repositorySummary": "",
            "localStartInstructions": "",
            "safeInspectionPaths": ["README.md", "src/", "app/", "tests/"],
            "sensitivePathPatterns": [
                ".env",
                ".env.*",
                "**/.env",
                "**/.env.*",
                "*secret*",
                "*credentials*",
                "*.pem",
                "*.key",
            ],
            "validationGoals": [],
            "knownRuntimeRequirements": [],
        }
        save_document(product_context_path, product_context)

    registry = load_registry(project)
    save_registry(project, registry)
    return workspace


def get_core_command(project: Path) -> str | None:
    workspace = load_document(layout.workspace_root(project) / layout.WORKSPACE_FILE, default={}) or {}
    return workspace.get("coreCommand")


def load_registry(project: Path) -> dict[str, Any]:
    return load_document(
        layout.registry_path(project),
        default={"schemaVersion": "proofsignal-spec-registry/v1", "useCases": [], "lastUpdatedAt": now_iso()},
    )


def save_registry(project: Path, registry: dict[str, Any]) -> None:
    registry.setdefault("schemaVersion", "proofsignal-spec-registry/v1")
    registry.setdefault("useCases", [])
    registry["lastUpdatedAt"] = now_iso()
    save_document(layout.registry_path(project), registry)


def load_use_case(project: Path, alias: str) -> UseCaseRecord:
    layout.ensure_path_safe_alias(alias)
    data = load_document(layout.use_case_path(project, alias))
    if not data:
        raise FileNotFoundError(f"Use case not found: {alias}")
    return UseCaseRecord.from_dict(data)


def save_use_case(project: Path, record: UseCaseRecord) -> None:
    layout.ensure_path_safe_alias(record.alias)
    save_document(layout.use_case_path(project, record.alias), record.to_dict())
    upsert_registry_entry(project, record)


def upsert_registry_entry(project: Path, record: UseCaseRecord) -> None:
    registry = load_registry(project)
    entry = {
        "alias": record.alias,
        "title": record.title,
        "targetSurface": record.targetSurface,
        "recordPath": f"{layout.WORKSPACE_DIR}/{layout.USE_CASES_DIR}/{record.alias}.yaml",
        "runnableStatus": record.status,
        "requiredRuntimeInputs": [item.name for item in record.runtimeInputs if item.kind != "credential"],
        "credentialGroups": [
            item.get("name", item) if isinstance(item, dict) else item for item in record.credentialGroups
        ],
        "lastResult": record.lastRun,
    }
    entries = [item for item in registry.get("useCases", []) if item.get("alias") != record.alias]
    entries.append(entry)
    entries.sort(key=lambda item: item.get("alias", ""))
    registry["useCases"] = entries
    save_registry(project, registry)


def list_use_cases(project: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    registry = load_registry(project)
    rows: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for item in registry.get("useCases", []):
        row = dict(item)
        try:
            record_path = layout.project_relative_path(project, row["recordPath"])
            if not record_path.exists():
                raise FileNotFoundError(row["recordPath"])
            record = UseCaseRecord.from_dict(load_document(record_path))
            row.update(
                {
                    "alias": record.alias,
                    "title": record.title,
                    "status": record.status,
                    "targetSurface": record.targetSurface,
                    "requiredRuntimeInputs": [entry.name for entry in record.runtimeInputs if entry.kind != "credential"],
                    "credentialGroups": [
                        cg.get("name", cg) if isinstance(cg, dict) else cg for cg in record.credentialGroups
                    ],
                    "lastResult": record.lastRun,
                }
            )
        except Exception as exc:  # keep list tolerant
            row["status"] = "invalid"
            warnings.append({"alias": item.get("alias"), "message": str(exc)})
        rows.append(row)
    return rows, warnings


def create_default_use_case(project: Path, alias: str, description: str) -> UseCaseRecord:
    layout.ensure_path_safe_alias(alias)
    title = alias.replace("-", " ").replace("_", " ").title()
    run_request_rel = f"{layout.WORKSPACE_DIR}/{layout.RUN_REQUESTS_DIR}/{alias}.yaml"
    skill_rel = f"{layout.WORKSPACE_DIR}/{layout.SKILLS_DIR}/{alias}.browser.md"
    return UseCaseRecord(
        alias=alias,
        title=title,
        description=description,
        runRequest=ArtifactReference(path=run_request_rel, kind="run-request", generated=True, id=f"request.{alias}", version="1.0.0"),
        mainSkill=ArtifactReference(path=skill_rel, kind="skill", generated=True, id=f"skill.{alias}", version="1.0.0"),
        skills=[ArtifactReference(path=skill_rel, kind="skill", generated=True, id=f"skill.{alias}", version="1.0.0")],
        runtimeInputs=[],
        credentialGroups=[],
    )


def resolve_artifacts(project: Path, alias: str) -> tuple[UseCaseRecord, Path, Path, list[Path]]:
    record = load_use_case(project, alias)
    if not record.runRequest:
        raise ValueError(f"Use case {alias} does not reference a run request.")
    if not record.mainSkill:
        raise ValueError(f"Use case {alias} does not reference a main skill.")
    run_request = layout.project_relative_path(project, record.runRequest.path)
    main_skill = layout.project_relative_path(project, record.mainSkill.path)
    skills = [layout.project_relative_path(project, skill.path) for skill in record.skills]
    for path in [run_request, main_skill, *skills]:
        if not path.exists():
            raise FileNotFoundError(path)
    return record, run_request, main_skill, skills


def update_validation(project: Path, alias: str, result: dict[str, Any]) -> UseCaseRecord:
    record = load_use_case(project, alias)
    status = result.get("status") or result.get("data", {}).get("status")
    record.validation = result
    record.status = "ready" if status == "passed" else "blocked"
    save_use_case(project, record)
    return record


def record_run(project: Path, entry: RunHistoryEntry) -> None:
    save_document(layout.run_history_path(project, entry.useCaseAlias, entry.runId), entry.to_dict())
    record = load_use_case(project, entry.useCaseAlias)
    record.lastRun = {
        "runId": entry.runId,
        "status": entry.status,
        "reportPath": entry.reportPath,
        "evidenceDir": entry.evidenceDir,
    }
    record.status = "ready" if entry.status == "passed" else "failed"
    save_use_case(project, record)


def detect_conflict(path: Path, expected_sha256: str | None, hash_func) -> bool:
    if not expected_sha256 or not path.exists():
        return False
    return hash_func(path.read_bytes()) != expected_sha256
