from __future__ import annotations

import json
import os
import hashlib
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from proofsignal_spec import __version__ as SPEC_VERSION

from . import layout
from .models import (
    ArtifactCapabilityPolicy,
    ArtifactCapabilityStamp,
    ArtifactReference,
    ConfirmationRequirement,
    CredentialReadinessHint,
    ReadinessSnapshot,
    RefreshImpactResult,
    RerunPolicy,
    RunHistoryEntry,
    SideEffectLifecycleDeclaration,
    UseCaseRecord,
)


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


def init_workspace(project: Path, force: bool = False, core_cmd: str | None = None, api_base_url: str | None = None) -> dict[str, Any]:
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
            "readinessDir": f"{layout.WORKSPACE_DIR}/{layout.READINESS_DIR}",
            "credentialHintsDir": f"{layout.WORKSPACE_DIR}/{layout.CREDENTIAL_HINTS_DIR}",
            "confirmationsDir": f"{layout.WORKSPACE_DIR}/{layout.CONFIRMATIONS_DIR}",
            "refreshImpactDir": f"{layout.WORKSPACE_DIR}/{layout.REFRESH_IMPACT_DIR}",
            "integrationsDir": f"{layout.WORKSPACE_DIR}/{layout.INTEGRATIONS_DIR}",
            "workflowsDir": f"{layout.WORKSPACE_DIR}/{layout.WORKFLOWS_DIR}",
        }
    )
    if core_cmd:
        workspace["coreCommand"] = core_cmd
    if api_base_url:
        workspace["entitlementApiBaseUrl"] = api_base_url
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

    workflow_definition = layout.workflow_definition_path(project, "proofsignal-use-case")
    if force or not workflow_definition.exists():
        save_document(
            workflow_definition,
            {
                "workflowId": "proofsignal-use-case",
                "name": "ProofSignal Use Case",
                "version": "1.0.0",
                "stages": ["understand", "specify", "clarify", "plan", "tasks", "implement", "validate", "run", "repair"],
                "requiredInputs": ["goal", "alias"],
            },
        )
    return workspace


def get_core_command(project: Path) -> str | None:
    workspace = load_document(layout.workspace_root(project) / layout.WORKSPACE_FILE, default={}) or {}
    return workspace.get("coreCommand")


def get_entitlement_api_base_url(project: Path) -> str | None:
    workspace = load_document(layout.workspace_root(project) / layout.WORKSPACE_FILE, default={}) or {}
    return workspace.get("entitlementApiBaseUrl")


def get_core_configuration(project: Path) -> dict[str, Any]:
    workspace = load_document(layout.workspace_root(project) / layout.WORKSPACE_FILE, default={}) or {}
    return {
        key: workspace.get(key)
        for key in [
            "coreCommand",
            "coreCommandSource",
            "coreConfiguredAt",
            "coreLastVerifiedAt",
            "coreVersion",
        ]
        if workspace.get(key) is not None
    }


def save_core_configuration(project: Path, core_cmd: str, *, source: str | None = None, version: str | None = None) -> dict[str, Any]:
    root = layout.workspace_root(project)
    workspace_path = root / layout.WORKSPACE_FILE
    if not workspace_path.exists():
        workspace = init_workspace(project)
    else:
        workspace = load_document(workspace_path, default={}) or {}
    timestamp = now_iso()
    if workspace.get("coreCommand") != core_cmd or not workspace.get("coreConfiguredAt"):
        workspace["coreConfiguredAt"] = timestamp
    workspace["coreCommand"] = core_cmd
    if source:
        workspace["coreCommandSource"] = source
    workspace["coreLastVerifiedAt"] = timestamp
    if version:
        workspace["coreVersion"] = version
    workspace["updatedAt"] = timestamp
    save_document(workspace_path, workspace)
    return workspace


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


def update_use_case_workflow_reference(project: Path, alias: str, workflow: dict[str, Any]) -> UseCaseRecord:
    record = load_use_case(project, alias)
    record.workflow = workflow
    save_use_case(project, record)
    return record


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
    if record.workflow:
        entry["workflow"] = {
            "currentStage": record.workflow.get("currentStage"),
            "workflowStatus": record.workflow.get("workflowStatus"),
            "lastWorkflowRunId": record.workflow.get("lastWorkflowRunId"),
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
            current = readiness_current_state(project, record)
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
                    "lastRun": _last_run_summary(record.lastRun),
                    "current": current,
                    "requirements": list_requirements(record),
                    "risk": list_risk(project, record),
                }
            )
        except Exception as exc:  # keep list tolerant
            row["status"] = "invalid"
            warnings.append({"alias": item.get("alias"), "message": str(exc)})
        rows.append(row)
    return rows, warnings


def _last_run_summary(last_run: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(last_run, dict):
        return {"status": "never-run", "runId": None}
    return {
        "status": last_run.get("status", "unknown"),
        "runId": last_run.get("runId"),
        "coreStatus": last_run.get("coreStatus"),
        "coverageStatus": last_run.get("coverageStatus"),
        "profile": last_run.get("profile"),
    }


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


def resolve_artifacts(project: Path, alias: str, *, core_contract: dict[str, Any] | None = None) -> tuple[UseCaseRecord, Path, Path, list[Path]]:
    record = load_use_case(project, alias)
    if not record.runRequest:
        raise ValueError(f"Use case {alias} does not reference a run request.")
    if not record.mainSkill:
        raise ValueError(f"Use case {alias} does not reference a main skill.")
    run_request = layout.project_relative_path(project, record.runRequest.path)
    main_skill = layout.project_relative_path(project, record.mainSkill.path)
    from proofsignal_spec.workflows.skill_execution_boundary import executable_skill_refs

    executable_refs = executable_skill_refs(record, core_contract=core_contract)
    skills = [layout.project_relative_path(project, skill.path) for skill in executable_refs]
    authored = [layout.project_relative_path(project, skill.path) for skill in [*record.skills, *record.sourceOnlySkills]]
    for path in [run_request, main_skill, *authored]:
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
        "coreStatus": entry.coreStatus,
        "coverageStatus": entry.coverageStatus,
        "profile": entry.profile,
        "profileSettings": entry.profileSettings,
        "selectedMainSkill": entry.selectedMainSkill,
        "executedSkill": entry.executedSkill,
        "skillSelectionStatus": entry.skillSelectionStatus,
        "gateCoverage": entry.gateCoverage,
        "missingRequiredGates": entry.missingRequiredGates,
        "partialCoverage": entry.partialCoverage,
        "runtimeContradictions": entry.runtimeContradictions,
        "repairRecommendations": entry.repairRecommendations,
        "sideEffects": entry.sideEffects,
        "runtimeOutputs": entry.runtimeOutputs,
        "resolvedRuntimeInputs": entry.resolvedRuntimeInputs,
        "postCommitInterpretation": entry.postCommitInterpretation,
        "rerunDecision": entry.rerunDecision,
        "sideEffectLifecycle": entry.sideEffectLifecycle,
        "reportPath": entry.reportPath,
        "evidenceDir": entry.evidenceDir,
    }
    record.status = "ready" if entry.status == "passed" else "failed"
    save_use_case(project, record)


def detect_conflict(path: Path, expected_sha256: str | None, hash_func) -> bool:
    if not expected_sha256 or not path.exists():
        return False
    return hash_func(path.read_bytes()) != expected_sha256


def artifact_fingerprints(project: Path, record: UseCaseRecord) -> dict[str, str]:
    fingerprints: dict[str, str] = {}
    refs: list[ArtifactReference] = []
    if record.runRequest:
        refs.append(record.runRequest)
    if record.mainSkill:
        refs.append(record.mainSkill)
    refs.extend(record.skills)
    refs.extend(record.sourceOnlySkills)
    for ref in refs:
        try:
            path = layout.project_relative_path(project, ref.path)
        except ValueError:
            continue
        if path.exists() and path.is_file():
            fingerprints[ref.path] = hashlib.sha256(path.read_bytes()).hexdigest()
    record_path = layout.use_case_path(project, record.alias)
    if record_path.exists():
        fingerprints[layout.to_project_relative(project, record_path)] = hashlib.sha256(record_path.read_bytes()).hexdigest()
    return fingerprints


def current_project_revision(project: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(project), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def save_readiness_snapshot(project: Path, snapshot: ReadinessSnapshot) -> None:
    save_document(layout.readiness_snapshot_path(project, snapshot.alias), snapshot.to_dict())


def load_readiness_snapshot(project: Path, alias: str) -> ReadinessSnapshot | None:
    data = load_document(layout.readiness_snapshot_path(project, alias), default=None)
    return ReadinessSnapshot.from_dict(data) if isinstance(data, dict) else None


def save_credential_readiness_hint(project: Path, hint: CredentialReadinessHint) -> None:
    save_document(layout.credential_hint_path(project, hint.credentialGroup.lower()), hint.to_dict())


def load_credential_readiness_hint(project: Path, group: str) -> CredentialReadinessHint | None:
    data = load_document(layout.credential_hint_path(project, group.lower()), default=None)
    return CredentialReadinessHint.from_dict(data) if isinstance(data, dict) else None


def credential_readiness_hints_for_record(project: Path, record: UseCaseRecord) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    for group in credential_runtime_requirements(record):
        hint = load_credential_readiness_hint(project, group["group"])
        hints.append(
            {
                "credentialGroup": group["group"],
                "expectedSource": group["source"],
                "requiredRuntimeNames": group["runtimeNames"],
                "preparationHint": hint.preparationHint if hint else "",
                "valuesIncluded": False,
            }
        )
    return hints


def save_confirmation_requirement(project: Path, requirement: ConfirmationRequirement) -> None:
    save_document(layout.confirmation_requirement_path(project, requirement.alias), requirement.to_dict())


def load_confirmation_requirement(project: Path, alias: str) -> ConfirmationRequirement | None:
    data = load_document(layout.confirmation_requirement_path(project, alias), default=None)
    return ConfirmationRequirement.from_dict(data) if isinstance(data, dict) else None


def save_refresh_impact(project: Path, impact: RefreshImpactResult) -> None:
    save_document(layout.refresh_impact_path(project, impact.alias), impact.to_dict())


def load_refresh_impact(project: Path, alias: str) -> RefreshImpactResult | None:
    data = load_document(layout.refresh_impact_path(project, alias), default=None)
    return RefreshImpactResult.from_dict(data) if isinstance(data, dict) else None


def save_capability_policy(project: Path, policy: ArtifactCapabilityPolicy) -> None:
    save_document(layout.capability_policy_path(project, policy.capability), policy.to_dict())


def load_capability_policy(project: Path, capability: str) -> ArtifactCapabilityPolicy | None:
    data = load_document(layout.capability_policy_path(project, capability), default=None)
    return ArtifactCapabilityPolicy.from_dict(data) if isinstance(data, dict) else None


def create_readiness_snapshot_from_validation(project: Path, alias: str, result: dict[str, Any]) -> ReadinessSnapshot:
    record = load_use_case(project, alias)
    status = "ready" if result.get("status") == "passed" else "blocked"
    managed = result.get("managedRuntimeReadiness") if isinstance(result.get("managedRuntimeReadiness"), dict) else {}
    runtime = result.get("runtimeReadiness") if isinstance(result.get("runtimeReadiness"), dict) else {}
    snapshot = ReadinessSnapshot(
        alias=alias,
        status=status,
        checkedAt=now_iso(),
        artifactFingerprints=artifact_fingerprints(project, record),
        specVersion=SPEC_VERSION,
        artifactContractVersion=record.schemaVersion,
        coreVersion=managed.get("runtimeVersion"),
        coreContractVersion=managed.get("contractVersion"),
        targetProjectRevision=current_project_revision(project),
        testedCodeScopeStatus="unknown",
        environmentBoundCredentialGroups=[item["group"] for item in credential_runtime_requirements(record)],
        sideEffectClass=side_effect_class(record),
        refreshImpactStatus=(load_refresh_impact(project, alias).status if load_refresh_impact(project, alias) else None),
        invalidationReasons=[],
        summary=result.get("readinessSummary") or runtime.get("message") or result.get("status"),
    )
    save_readiness_snapshot(project, snapshot)
    return snapshot


def readiness_current_state(project: Path, record: UseCaseRecord) -> dict[str, Any]:
    snapshot = load_readiness_snapshot(project, record.alias)
    last_run = record.lastRun if isinstance(record.lastRun, dict) else None
    if not snapshot:
        return {
            "status": "not-checked",
            "label": "Not checked",
            "checked": False,
            "checkedAt": None,
            "reasons": ["No current readiness snapshot has been recorded."],
            "lastRunStatus": last_run.get("status") if last_run else None,
        }
    reasons = snapshot_invalidation_reasons(project, record, snapshot)
    status = "ready" if snapshot.status == "ready" and not reasons else "needs-validate"
    if snapshot.status == "blocked":
        status = "blocked"
    if reasons and any(item["code"] in {"age-expired", "artifact-changed", "target-revision-changed", "write-post-commit-risk"} for item in reasons):
        status = "stale"
    return {
        "status": status,
        "label": _current_label(status),
        "checked": True,
        "checkedAt": snapshot.checkedAt,
        "ageSeconds": _snapshot_age_seconds(snapshot),
        "reasons": [item["message"] for item in reasons],
        "invalidationReasons": reasons,
        "snapshotStatus": snapshot.status,
        "lastRunStatus": last_run.get("status") if last_run else None,
        "environmentBoundCredentialGroups": snapshot.environmentBoundCredentialGroups,
        "testedCodeScopeStatus": snapshot.testedCodeScopeStatus,
    }


def snapshot_invalidation_reasons(project: Path, record: UseCaseRecord, snapshot: ReadinessSnapshot) -> list[dict[str, str]]:
    reasons: list[dict[str, str]] = []
    current_fingerprints = artifact_fingerprints(project, record)
    for path, old_hash in snapshot.artifactFingerprints.items():
        if current_fingerprints.get(path) != old_hash:
            reasons.append({"code": "artifact-changed", "message": f"Artifact changed since readiness check: {path}"})
            break
    if snapshot.specVersion and snapshot.specVersion != SPEC_VERSION:
        reasons.append({"code": "spec-version-changed", "message": f"Spec version changed from {snapshot.specVersion} to {SPEC_VERSION}."})
    current_revision = current_project_revision(project)
    if snapshot.targetProjectRevision and current_revision and snapshot.targetProjectRevision != current_revision:
        reasons.append({"code": "target-revision-changed", "message": "Target project revision changed since readiness check."})
    max_age_hours = 24 if _risk_requires_short_snapshot(record) else 24 * 7
    age_seconds = _snapshot_age_seconds(snapshot)
    if age_seconds is None or age_seconds > max_age_hours * 3600:
        reasons.append({"code": "age-expired", "message": f"Readiness snapshot is older than the {max_age_hours} hour risk threshold."})
    if snapshot.environmentBoundCredentialGroups:
        reasons.append({"code": "environment-bound", "message": "Snapshot depends on credential/environment state and does not guarantee the current process."})
    if _last_run_has_write_risk(record):
        reasons.append({"code": "write-post-commit-risk", "message": "Previous write run has inferred or unknown post-commit activity."})
    impact = load_refresh_impact(project, record.alias)
    if impact and impact.status in {"affected", "unknown"}:
        reasons.append({"code": f"refresh-impact-{impact.status}", "message": impact.reason or f"Understanding refresh impact is {impact.status}."})
    return reasons


def list_requirements(record: UseCaseRecord) -> dict[str, Any]:
    return {
        "runtimeInputs": [item.name for item in record.runtimeInputs if item.kind != "credential"],
        "credentials": credential_runtime_requirements(record),
        "sideEffectClass": side_effect_class(record),
        "cleanupPolicy": lifecycle_declaration(record).cleanupPolicy,
    }


def list_risk(project: Path, record: UseCaseRecord) -> dict[str, Any]:
    confirmation = load_confirmation_requirement(project, record.alias)
    capability = record.artifactCapabilities if isinstance(record.artifactCapabilities, dict) else {}
    return {
        "classes": _risk_classes(record),
        "write": side_effect_class(record) in {"write", "external-notification"},
        "cleanupPolicy": lifecycle_declaration(record).cleanupPolicy,
        "cleanupDeclared": lifecycle_declaration(record).cleanupPolicy != "not-declared",
        "capabilityStatus": capability.get("status", "legacy-or-unknown" if not capability else "unknown"),
        "requiresConfirmation": bool(confirmation and confirmation.blocksExecution),
        "confirmationId": confirmation.id if confirmation else None,
    }


def credential_runtime_requirements(record: UseCaseRecord) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    refs = record.credentialRefs if isinstance(record.credentialRefs, dict) else {}
    for group, data in refs.items():
        if not isinstance(data, dict):
            continue
        keys = data.get("keys") if isinstance(data.get("keys"), dict) else {}
        groups.append(
            {
                "group": str(group),
                "source": str(data.get("source") or "environment"),
                "runtimeNames": [str(value) for value in keys.values() if value],
                "fields": sorted(str(key) for key in keys),
            }
        )
    for group in record.credentialGroups:
        name = group.get("name") if isinstance(group, dict) else group
        if name and not any(item["group"] == str(name) for item in groups):
            groups.append({"group": str(name), "source": "unknown", "runtimeNames": [], "fields": []})
    return groups


def side_effect_class(record: UseCaseRecord) -> str:
    data = record.sideEffects if isinstance(record.sideEffects, dict) else {}
    return str(data.get("class") or data.get("sideEffectClass") or "none")


def lifecycle_declaration(record: UseCaseRecord) -> SideEffectLifecycleDeclaration:
    side_effects = record.sideEffects if isinstance(record.sideEffects, dict) else {}
    lifecycle = record.sideEffectLifecycle or side_effects.get("lifecycle")
    return SideEffectLifecycleDeclaration.from_dict(lifecycle if isinstance(lifecycle, dict) else None)


def capability_stamp(capabilities: list[str], *, contract_version: str, authored_at: str | None = None) -> dict[str, Any]:
    return ArtifactCapabilityStamp(
        specVersion=SPEC_VERSION,
        artifactContractVersion=contract_version,
        authoredAt=authored_at or now_iso(),
        capabilities=capabilities,
    ).to_dict()


def confirmation_requirement(
    *,
    alias: str,
    risk_class: str,
    scope: str,
    reason: str,
    recommended_action: str,
    blocks_execution: bool = True,
) -> ConfirmationRequirement:
    return ConfirmationRequirement(
        id=f"confirm.{alias}.{scope}",
        alias=alias,
        riskClass=risk_class,
        scope=scope,
        reason=reason,
        recommendedAction=recommended_action,
        blocksExecution=blocks_execution,
        expiresWhen=[
            "use-case artifact changes",
            "run request changes",
            "main skill changes",
            "target project revision changes",
            "24 hours pass for write or credentialed use cases",
        ],
    )


def run_confirmation_requirements(project: Path, record: UseCaseRecord) -> list[ConfirmationRequirement]:
    requirements: list[ConfirmationRequirement] = []
    side_effect = side_effect_class(record)
    if side_effect not in {"write", "external-notification"}:
        return requirements
    lifecycle = lifecycle_declaration(record)
    capabilities = _capability_names(record)
    legacy = not capabilities
    if lifecycle.cleanupPolicy == "not-declared":
        requirements.append(
            confirmation_requirement(
                alias=record.alias,
                risk_class=side_effect,
                scope="missing-side-effect-lifecycle",
                reason=(
                    "Legacy write/external-notification artifact has no cleanup lifecycle declaration."
                    if legacy
                    else "Write/external-notification artifact has no cleanup lifecycle declaration."
                ),
                recommended_action="Migrate the artifact to declare cleanup lifecycle before future write runs.",
            )
        )
    safety_capabilities = {"explicit-confirmation", "side-effect-lifecycle", "write-activity-interpretation"}
    if not safety_capabilities <= capabilities:
        missing = sorted(safety_capabilities - capabilities) if capabilities else sorted(safety_capabilities)
        requirements.append(
            confirmation_requirement(
                alias=record.alias,
                risk_class=side_effect,
                scope="legacy-missing-safety-capability",
                reason=f"Artifact is missing safety capability metadata: {', '.join(missing)}.",
                recommended_action="Migrate or re-persist the artifact so current write safety capabilities are declared.",
            )
        )
    if _post_commit_rerun_requires_confirmation(record):
        requirements.append(
            confirmation_requirement(
                alias=record.alias,
                risk_class=side_effect,
                scope="post-commit-rerun",
                reason="Previous write run has inferred, confirmed, or unknown post-commit activity.",
                recommended_action="Clean up, refresh generated inputs, declare idempotency, or explicitly confirm rerun risk.",
            )
        )
    impact = load_refresh_impact(project, record.alias)
    if impact and impact.status == "unknown":
        requirements.append(
            confirmation_requirement(
                alias=record.alias,
                risk_class=side_effect,
                scope="unknown-refresh-impact",
                reason=impact.reason or "Refresh impact on this write use case is unknown.",
                recommended_action="Validate or refresh understanding before executing, or explicitly confirm the write risk.",
            )
        )
    if requirements:
        save_confirmation_requirement(project, requirements[0])
    return requirements


def side_effect_lifecycle_summary(record: UseCaseRecord, runtime_outputs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    lifecycle = lifecycle_declaration(record)
    outputs = runtime_outputs or []
    refs = [
        {"name": item.get("name"), "source": item.get("source"), "value": item.get("value"), "status": item.get("status")}
        for item in outputs
        if isinstance(item, dict) and item.get("value")
    ]
    return {
        "cleanupPolicy": lifecycle.cleanupPolicy,
        "cleanupRequired": lifecycle.cleanupRequired,
        "trackingIntent": lifecycle.trackingIntent,
        "instructions": lifecycle.instructions,
        "declared": lifecycle.cleanupPolicy != "not-declared",
        "resourceRefs": refs,
        "status": "not-declared" if lifecycle.cleanupPolicy == "not-declared" else "declared",
    }


def _risk_requires_short_snapshot(record: UseCaseRecord) -> bool:
    return bool(credential_runtime_requirements(record)) or side_effect_class(record) in {"write", "external-notification"}


def _last_run_has_write_risk(record: UseCaseRecord) -> bool:
    last_run = record.lastRun if isinstance(record.lastRun, dict) else {}
    interpretation = last_run.get("postCommitInterpretation") if isinstance(last_run.get("postCommitInterpretation"), dict) else {}
    return bool(interpretation.get("postCommit") or interpretation.get("sideEffectMayExist") or interpretation.get("sideEffectStatus") == "unknown")


def _post_commit_rerun_requires_confirmation(record: UseCaseRecord) -> bool:
    if not _last_run_has_write_risk(record):
        return False
    policy = RerunPolicy.from_dict(record.rerunPolicy)
    if policy.afterCommit == "blocked":
        return False
    if policy.afterCommit == "allowed-with-new-inputs":
        refreshable = {item.name for item in record.runtimeInputs if item.source == "generated" and item.refreshOnRerunAfterCommit}
        return not bool(set(policy.refreshRuntimeInputs) & refreshable)
    return policy.afterCommit in {"requires-confirmation", "allowed"}


def _risk_classes(record: UseCaseRecord) -> list[str]:
    classes: list[str] = []
    if credential_runtime_requirements(record):
        classes.append("credentialed")
    side_effect = side_effect_class(record)
    if side_effect in {"write", "external-notification"}:
        classes.append(side_effect)
    if _last_run_has_write_risk(record):
        classes.append("post-commit")
    if not classes:
        classes.append("read-only")
    return classes


def _capability_names(record: UseCaseRecord) -> set[str]:
    raw = record.artifactCapabilities if isinstance(record.artifactCapabilities, dict) else {}
    if isinstance(raw.get("capabilities"), list):
        return {str(item) for item in raw.get("capabilities", [])}
    stamp = raw.get("stamp") if isinstance(raw.get("stamp"), dict) else {}
    if isinstance(stamp.get("capabilities"), list):
        return {str(item) for item in stamp.get("capabilities", [])}
    return set()


def _snapshot_age_seconds(snapshot: ReadinessSnapshot) -> int | None:
    try:
        checked = datetime.fromisoformat(snapshot.checkedAt.replace("Z", "+00:00"))
    except ValueError:
        return None
    if checked.tzinfo is None:
        checked = checked.replace(tzinfo=UTC)
    return int((datetime.now(UTC) - checked.astimezone(UTC)).total_seconds())


def _current_label(status: str) -> str:
    labels = {
        "ready": "Last checked ready",
        "not-checked": "Not checked",
        "stale": "Needs validation",
        "needs-validate": "Needs validation",
        "blocked": "Blocked",
    }
    return labels.get(status, "Unknown")
