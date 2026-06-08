from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from proofsignal_spec.workspace.models import ArtifactReference, UseCaseRecord


BOUNDARY_CATEGORY = "skill-execution-boundary"
SINGLE_MAIN_MODE = "single-main"
CORE_MULTI_SKILL_MODE = "core-declared-multi-skill"
PARTIAL_SUPPORT_MODE = "partial-support"


@dataclass(slots=True)
class MultiSkillCapability:
    supported: bool = False
    mode: Literal["single-main", "core-declared-multi-skill", "partial-support"] = SINGLE_MAIN_MODE
    roles: list[str] = field(default_factory=list)
    ordering: str | None = None
    evidenceSemantics: str | None = None
    partialExecutableRoles: list[str] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value not in (None, [], {})}


@dataclass(slots=True)
class ExecutionBoundaryDecision:
    mode: str
    mainSkill: ArtifactReference | None
    executableSkills: list[ArtifactReference] = field(default_factory=list)
    sourceOnlySkills: list[ArtifactReference] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "mainSkill": self.mainSkill.to_dict() if self.mainSkill else None,
            "executableSkills": [item.to_dict() for item in self.executableSkills],
            "sourceOnlySkills": [item.to_dict() for item in self.sourceOnlySkills],
            "findings": self.findings,
        }


def multi_skill_capability(core_contract: dict[str, Any] | None) -> MultiSkillCapability:
    """Project Core-declared multi-skill support from public contract metadata."""

    if not isinstance(core_contract, dict):
        return MultiSkillCapability(
            findings=[
                _finding(
                    "skill-execution.single-main",
                    "info",
                    "Core contract is unavailable; Spec uses single-main execution.",
                )
            ]
        )
    sections = core_contract.get("sections") if isinstance(core_contract.get("sections"), dict) else {}
    raw = (
        sections.get("skillExecution")
        or sections.get("multiSkillExecution")
        or sections.get("executableSkills")
        or {}
    )
    if not isinstance(raw, dict):
        return MultiSkillCapability(
            findings=[
                _finding(
                    "skill-execution.single-main",
                    "info",
                    "Core contract does not declare deterministic multi-skill execution; Spec uses single-main execution.",
                )
            ]
        )
    status = str(raw.get("status") or raw.get("supportStatus") or "").lower()
    if status in {"partial", "partially-supported", "preconditions-only"}:
        partial_roles = _role_names(raw.get("roles") or raw.get("supportedRoles"))
        return MultiSkillCapability(
            supported=False,
            mode=PARTIAL_SUPPORT_MODE,
            partialExecutableRoles=partial_roles,
            findings=[
                _finding(
                    "skill-execution.partial-support",
                    "warning",
                    "Core declares only partial skill execution support; unsupported browser skills must be composed or source-only.",
                )
            ],
        )
    if status not in {"stable", "supported"}:
        return MultiSkillCapability(
            findings=[
                _finding(
                    "skill-execution.single-main",
                    "info",
                    "Core contract does not declare stable multi-skill execution; Spec uses single-main execution.",
                )
            ]
        )
    roles = _role_names(raw.get("roles") or raw.get("supportedRoles"))
    ordering = raw.get("ordering") or raw.get("order") or raw.get("executionOrder")
    evidence = raw.get("evidenceSemantics") or raw.get("evidence") or raw.get("gateEvidence")
    if not roles or not ordering or not evidence:
        return MultiSkillCapability(
            findings=[
                _finding(
                    "skill-execution.multi-skill-contract-incomplete",
                    "blocking",
                    "Core multi-skill support is missing declared roles, ordering, or evidence semantics.",
                )
            ]
        )
    return MultiSkillCapability(
        supported=True,
        mode=CORE_MULTI_SKILL_MODE,
        roles=roles,
        ordering=str(ordering),
        evidenceSemantics=str(evidence),
    )


def resolve_execution_boundary(
    record: UseCaseRecord,
    *,
    core_contract: dict[str, Any] | None = None,
    run_request: dict[str, Any] | None = None,
) -> ExecutionBoundaryDecision:
    capability = multi_skill_capability(core_contract)
    main = record.mainSkill
    authored = _dedupe_refs([*(record.skills or []), *(record.sourceOnlySkills or [])])
    if main and all(item.path != main.path for item in authored):
        authored.insert(0, main)

    if capability.supported:
        source_only_paths = {item.path for item in record.sourceOnlySkills}
        executable_candidates = [main] if main else []
        executable_candidates.extend(item for item in record.skills if item.path not in source_only_paths)
        executable = _dedupe_refs(executable_candidates)
        return ExecutionBoundaryDecision(
            mode=CORE_MULTI_SKILL_MODE,
            mainSkill=main,
            executableSkills=executable,
            sourceOnlySkills=_dedupe_refs([*record.sourceOnlySkills, *_source_only_refs(authored, executable)]),
            findings=capability.findings,
        )

    executable = [main] if main else []
    source_only = _dedupe_refs([*record.sourceOnlySkills, *_source_only_refs(authored, executable)])
    findings = list(capability.findings)
    if _unclassified_non_main_skills(record, main):
        findings.append(
            _finding(
                "skill-execution.multiple-unsupported",
                "blocking",
                "Use case metadata exposes multiple executable skill candidates while Core does not support multi-skill execution.",
            )
        )
    if _run_request_contains_source_only_skill(run_request, source_only):
        findings.append(
            _finding(
                "skill-execution.reusable-marked-executable",
                "blocking",
                "Run request lists a reusable source-only skill as executable while Core does not support multi-skill execution.",
            )
        )
    if _run_request_executable_count(run_request) > len(executable):
        findings.append(
            _finding(
                "skill-execution.legacy-migration-required",
                "blocking",
                "Legacy run request lists multiple executable skills, including source-only/helper skills, while Core does not support multi-skill execution.",
            )
        )
    return ExecutionBoundaryDecision(
        mode=SINGLE_MAIN_MODE,
        mainSkill=main,
        executableSkills=executable,
        sourceOnlySkills=source_only,
        findings=findings,
    )


def executable_skill_refs(record: UseCaseRecord, *, core_contract: dict[str, Any] | None = None) -> list[ArtifactReference]:
    return resolve_execution_boundary(record, core_contract=core_contract).executableSkills


def source_only_skill_refs(record: UseCaseRecord, *, core_contract: dict[str, Any] | None = None) -> list[ArtifactReference]:
    return resolve_execution_boundary(record, core_contract=core_contract).sourceOnlySkills


def _role_names(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    names: list[str] = []
    for item in value:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict):
            status = str(item.get("status") or "stable").lower()
            if status in {"stable", "supported"}:
                name = item.get("name") or item.get("role")
                if name:
                    names.append(str(name))
    return names


def _source_only_refs(authored: list[ArtifactReference], executable: list[ArtifactReference]) -> list[ArtifactReference]:
    executable_paths = {item.path for item in executable}
    return [item for item in authored if item.path not in executable_paths]


def _dedupe_refs(items: list[ArtifactReference | None]) -> list[ArtifactReference]:
    deduped: list[ArtifactReference] = []
    seen: set[str] = set()
    for item in items:
        if item is None or item.path in seen:
            continue
        seen.add(item.path)
        deduped.append(item)
    return deduped


def _run_request_executable_count(run_request: dict[str, Any] | None) -> int:
    if not isinstance(run_request, dict):
        return 0
    skills = run_request.get("skills")
    if isinstance(skills, list):
        return len(skills)
    return 0


def _run_request_contains_source_only_skill(run_request: dict[str, Any] | None, source_only: list[ArtifactReference]) -> bool:
    if not isinstance(run_request, dict) or not source_only:
        return False
    skills = run_request.get("skills")
    if not isinstance(skills, list):
        return False
    source_ids = {item.id for item in source_only if item.id}
    source_paths = {item.path for item in source_only if item.path}
    for skill in skills:
        if not isinstance(skill, dict):
            continue
        skill_id = skill.get("id") or skill.get("skillId")
        skill_path = skill.get("path")
        if (skill_id and str(skill_id) in source_ids) or (skill_path and str(skill_path) in source_paths):
            return True
    return False


def _unclassified_non_main_skills(record: UseCaseRecord, main: ArtifactReference | None) -> list[ArtifactReference]:
    if not main:
        return []
    source_paths = {item.path for item in record.sourceOnlySkills}
    return [item for item in record.skills if item.path != main.path and item.path not in source_paths]


def _finding(code: str, severity: str, message: str) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "category": BOUNDARY_CATEGORY,
        "message": message,
        "recoveryAction": "Compose helper behavior into the main skill or reclassify helper skills as source-only metadata.",
        "repairable": code != "skill-execution.multi-skill-contract-incomplete",
    }
