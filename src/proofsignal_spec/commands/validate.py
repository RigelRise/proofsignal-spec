from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.core.adapter import CoreAdapter
from proofsignal_spec.workflows.models import WORKFLOW_VALIDATION_READINESS_SCHEMA, CoreReadiness, ReadinessBlocker
from proofsignal_spec.workflows.authoring_coherence import evaluate_persisted_coherence
from proofsignal_spec.workflows.readiness import structural_validation, validation_readiness
from proofsignal_spec.workflows.runtime_readiness import evaluate_runtime_readiness
from proofsignal_spec.workspace.repository import get_core_command, resolve_artifacts, update_validation


def _selected_main_skill(record_main_skill: Any, main_skill: Path) -> dict[str, Any]:
    data: dict[str, Any] = {"path": str(record_main_skill.path if record_main_skill else main_skill)}
    if record_main_skill and record_main_skill.id:
        data["id"] = record_main_skill.id
    if record_main_skill and record_main_skill.version:
        data["version"] = record_main_skill.version
    return data


def run(project: Path, alias: str, runtime_readiness: bool = False, core_cmd: str | None = None) -> dict[str, Any]:
    structural = structural_validation(project, alias=alias)
    if structural.status == "blocked":
        return {
            "schemaVersion": WORKFLOW_VALIDATION_READINESS_SCHEMA,
            "alias": alias,
            "status": "blocked",
            "structuralValidation": structural.to_dict(),
            "coreReadiness": CoreReadiness(status="error", message="Core readiness was not checked because structural workspace validation is blocked.").to_dict(),
            "blockers": [
                ReadinessBlocker(
                    code="workspace.structural-blocked",
                    message="Workspace structure is blocked. Review structuralValidation.findings and apply approved migrations when offered.",
                    recoveryCommand=f"proofsignal-spec workflow check validate --alias {alias} --json",
                ).to_dict()
            ],
        }
    readiness = validation_readiness(project, alias=alias, core_cmd=core_cmd)
    if readiness.get("status") != "ready":
        return readiness
    record, run_request, main_skill, skills = resolve_artifacts(project, alias)
    coherence = evaluate_persisted_coherence(project, alias)
    if coherence.status == "blocked":
        result = {
            "schemaVersion": WORKFLOW_VALIDATION_READINESS_SCHEMA,
            "alias": alias,
            "status": "blocked",
            "selectedMainSkill": _selected_main_skill(record.mainSkill, main_skill),
            "authoringCoherence": coherence.to_dict(),
            "blockers": [
                ReadinessBlocker(
                    code="authoring.coherence-blocked",
                    message=message,
                    recoveryCommand=f"proofsignal-spec workflow persist implement --alias {alias} --payload <payload.json> --json",
                ).to_dict()
                for message in coherence.blockers
            ],
        }
        update_validation(project, alias, result)
        return result
    result = CoreAdapter(executable=core_cmd or get_core_command(project), cwd=project).authoring_check(run_request, main_skill, skills, runtime_readiness=runtime_readiness)
    runtime_check = evaluate_runtime_readiness(project, alias, authoring_result=result) if runtime_readiness else None
    wrapped = {
        "alias": alias,
        "status": result.get("status", "error"),
        "selectedMainSkill": _selected_main_skill(record.mainSkill, main_skill),
        "skillSelectionStatus": "matched",
        "authoringCoherence": coherence.to_dict(),
        "core": result,
    }
    if runtime_check:
        wrapped["runtimeReadiness"] = runtime_check.to_dict()
        if runtime_check.status != "passed":
            wrapped["status"] = "blocked"
            wrapped["blockers"] = [
                ReadinessBlocker(
                    code=finding,
                    message=runtime_check.message or "Runtime readiness is blocked.",
                    recoveryCommand=f"proofsignal-spec workflow check validate --alias {alias} --json",
                ).to_dict()
                for finding in runtime_check.findingIds
            ]
    update_validation(project, alias, wrapped)
    return wrapped
