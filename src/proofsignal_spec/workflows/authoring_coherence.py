from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.workspace import layout

from .evidence import browser_from_skill_content, browser_from_skill_path, extract_browser_evidence, merge_evidence, normalize_planned_gates
from .gate_coverage import calculate_gate_coverage
from .models import AuthoringCoherenceResult
from .repository import load_artifact_plan
from .skill_execution_boundary import multi_skill_capability

ACCEPTED_ARTIFACT_FIELDS = ["path", "kind", "content", "intent", "browser"]
NORMALIZED_ALIASES = {"artifactPath": "path", "artifactKind": "kind"}


def normalize_artifact_aliases(value: Any) -> Any:
    if isinstance(value, dict):
        normalized = {NORMALIZED_ALIASES.get(str(key), key): normalize_artifact_aliases(item) for key, item in value.items()}
        return normalized
    if isinstance(value, list):
        return [normalize_artifact_aliases(item) for item in value]
    return value


def normalized_aliases_used(value: Any) -> list[str]:
    used: set[str] = set()
    _collect_aliases(value, used)
    return sorted(used)


def evaluate_implementation_coherence(
    project: Path,
    alias: str,
    content: dict[str, Any],
    *,
    new_artifacts: bool = True,
    core_contract: dict[str, Any] | None = None,
) -> AuthoringCoherenceResult:
    result = AuthoringCoherenceResult(alias=alias)
    result.normalizedAliases = normalized_aliases_used(content)

    try:
        plan = load_artifact_plan(project, alias)
    except Exception as exc:
        result.status = "warning"
        result.warnings.append(f"Artifact plan unavailable; authoring coherence checks are limited: {exc}")
        return result

    result.mainSkill = plan.mainSkill
    gates, gate_warnings = normalize_planned_gates(plan.validationGates)
    result.warnings.extend(gate_warnings)
    if not gates:
        result.status = "warning"
        result.warnings.append("No planned validation gates were found; run results cannot be reported as complete planned validation.")
        return result

    skill_artifacts = _skill_artifacts(content)
    skill_paths = [_artifact_path(item) for item in skill_artifacts]
    if plan.mainSkill not in skill_paths:
        result.blockers.append(
            f"Planned main validation skill is missing: {plan.mainSkill}. Accepted artifact fields: {', '.join(ACCEPTED_ARTIFACT_FIELDS)}."
        )

    malformed = [str(item) for item in skill_artifacts if not _artifact_path(item)]
    if malformed:
        result.blockers.append(
            "Implementation payload contains skill artifacts without a valid path. "
            f"Accepted field names include path/kind; aliases artifactPath/artifactKind are normalized. Planned main skill: {plan.mainSkill}."
        )

    executable_artifacts = _executable_skill_artifacts(skill_artifacts, plan, core_contract=core_contract)
    source_only_artifacts = [item for item in skill_artifacts if item not in executable_artifacts]
    if source_only_artifacts:
        result.warnings.append(
            f"{len(source_only_artifacts)} source-only skill artifact(s) are excluded from executable gate coverage."
        )

    evidence = merge_evidence(
        [
            extract_browser_evidence(
                _browser_for_artifact(project, artifact),
                source_artifact=_artifact_path(artifact),
                known_gate_ids={gate.id for gate in gates},
                core_contract=core_contract,
            )
            for artifact in executable_artifacts
            if _artifact_path(artifact)
        ]
    )
    result.blockers.extend(evidence.blockers)
    result.warnings.extend(evidence.warnings)
    if evidence.unmappedEvidence:
        result.warnings.append(
            f"{len(evidence.unmappedEvidence)} evidence item(s) lack a valid gateId and will not count toward planned gate coverage."
        )

    coverage = calculate_gate_coverage(gates, evidence)
    result.gateCoverage = coverage
    for item in coverage:
        gate = next((gate for gate in gates if gate.id == item.gateId), None)
        if not gate or gate.legacy:
            continue
        if gate.required and item.status in {"missing", "network-only", "screenshot-only", "not-evaluated"}:
            message = f"Required gate {item.gateId} is {item.status}; specific UI evidence mapped by gateId is required."
            if new_artifacts:
                result.blockers.append(message)
            else:
                result.warnings.append(message)

    if result.blockers:
        result.status = "blocked"
    elif result.warnings:
        result.status = "warning"
    else:
        result.status = "passed"
    return result


def evaluate_persisted_coherence(project: Path, alias: str, *, core_contract: dict[str, Any] | None = None) -> AuthoringCoherenceResult:
    try:
        from proofsignal_spec.workspace.repository import load_use_case

        record = load_use_case(project, alias)
    except Exception as exc:
        result = AuthoringCoherenceResult(alias=alias, status="blocked")
        result.blockers.append(str(exc))
        return result
    content = {
        "skills": [
            {
                "path": skill.path,
                "kind": skill.kind,
                "content": _read_text(project, skill.path),
            }
            for skill in record.skills
        ]
    }
    return evaluate_implementation_coherence(project, alias, content, new_artifacts=False, core_contract=core_contract)


def _skill_artifacts(content: dict[str, Any]) -> list[dict[str, Any]]:
    skills = content.get("skills")
    if isinstance(skills, list):
        return [item for item in skills if isinstance(item, dict)]
    artifacts = content.get("artifacts")
    if isinstance(artifacts, list):
        return [
            item
            for item in artifacts
            if isinstance(item, dict)
            and (_artifact_kind(item) == "skill" or str(_artifact_path(item)).endswith(".browser.md"))
        ]
    return []


def _executable_skill_artifacts(
    skill_artifacts: list[dict[str, Any]],
    plan: Any,
    *,
    core_contract: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    capability = multi_skill_capability(core_contract)
    if capability.supported:
        source_only_paths = set(getattr(plan, "sourceOnlySkills", []) or [])
        return [item for item in skill_artifacts if _artifact_path(item) not in source_only_paths]
    return [item for item in skill_artifacts if _artifact_path(item) == plan.mainSkill]


def _browser_for_artifact(project: Path, artifact: dict[str, Any]) -> dict[str, Any]:
    browser = artifact.get("browser")
    if isinstance(browser, dict):
        return browser
    intent = artifact.get("intent") if isinstance(artifact.get("intent"), dict) else {}
    if isinstance(intent.get("browser"), dict):
        return intent["browser"]
    content = artifact.get("content")
    if isinstance(content, str) and content.strip():
        return browser_from_skill_content(content)
    path = _artifact_path(artifact)
    if path:
        try:
            return browser_from_skill_path(layout.project_relative_path(project, path))
        except Exception:
            return {}
    return {}


def _artifact_path(item: dict[str, Any]) -> str:
    return str(item.get("path") or item.get("name") or "")


def _artifact_kind(item: dict[str, Any]) -> str:
    return str(item.get("kind") or "")


def _read_text(project: Path, rel_path: str) -> str:
    try:
        path = layout.project_relative_path(project, rel_path)
        return path.read_text(encoding="utf-8") if path.exists() else ""
    except Exception:
        return ""


def _collect_aliases(value: Any, used: set[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in NORMALIZED_ALIASES:
                used.add(str(key))
            _collect_aliases(item, used)
    elif isinstance(value, list):
        for item in value:
            _collect_aliases(item, used)
