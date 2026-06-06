from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.core.adapter import CoreAdapter
from proofsignal_spec.core.contracts import core_entitlement_blocker_code
from proofsignal_spec.runtime.entitlement import load_receipt, receipt_status
from proofsignal_spec.runtime.models import RuntimeSetupBlocker
from proofsignal_spec.runtime.resolver import ensure_core_runtime
from proofsignal_spec.workflows.first_run import advance_guided_first_run_state
from proofsignal_spec.workflows.models import WORKFLOW_VALIDATION_READINESS_SCHEMA, CoreReadiness, ReadinessBlocker, ValidationReadinessSummary
from proofsignal_spec.workflows.authoring_coherence import evaluate_persisted_coherence
from proofsignal_spec.workflows.readiness import (
    executable_contract_blockers,
    legacy_executable_artifact_blockers,
    managed_runtime_contract_blockers,
    structural_validation,
    validation_readiness,
)
from proofsignal_spec.workflows.runtime_readiness import evaluate_runtime_readiness
from proofsignal_spec.workspace.repository import resolve_artifacts, update_validation


def _selected_main_skill(record_main_skill: Any, main_skill: Path) -> dict[str, Any]:
    data: dict[str, Any] = {"path": str(record_main_skill.path if record_main_skill else main_skill)}
    if record_main_skill and record_main_skill.id:
        data["id"] = record_main_skill.id
    if record_main_skill and record_main_skill.version:
        data["version"] = record_main_skill.version
    return data


def run(project: Path, alias: str, runtime_readiness: bool = False, core_cmd: str | None = None, api_base_url: str | None = None) -> dict[str, Any]:
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
                    recoveryCommand=f"proofsignal workflow check validate --alias {alias} --json",
                ).to_dict()
            ],
        }
    managed_runtime = ensure_core_runtime(project, explicit_core_cmd=core_cmd, api_base_url=api_base_url, context="validate")
    if managed_runtime.status != "ready":
        contract_blockers = managed_runtime_contract_blockers(managed_runtime)
        result = {
            "schemaVersion": WORKFLOW_VALIDATION_READINESS_SCHEMA,
            "capabilitySchemaVersion": "proofsignal-spec-workflow-capability/v1",
            "requiredCapability": "workflow.guardrails/v1",
            "supported": True,
            "stage": "validate",
            "alias": alias,
            "status": "blocked",
            "structuralValidation": structural.to_dict(),
            "coreReadiness": CoreReadiness(
                status="incompatible" if managed_runtime.status == "incompatible" else "missing",
                coreCommand=managed_runtime.runtimeCommand,
                version=managed_runtime.runtimeVersion,
                contractVersion=managed_runtime.contractVersion or "",
                missingOperations=managed_runtime.missingOperations,
                incompatibleOperations=managed_runtime.incompatibleOperations,
                message=managed_runtime.message,
            ).to_dict(),
            "managedRuntimeReadiness": managed_runtime.to_dict(),
            "blockers": [blocker.to_dict() for blocker in contract_blockers]
            or [
                ReadinessBlocker.from_dict(blocker.to_dict()).to_dict()
                for blocker in managed_runtime.blockers
            ],
        }
        update_validation(project, alias, result)
        return result
    record, run_request, main_skill, skills = resolve_artifacts(project, alias)
    contract_blockers = [
        *legacy_executable_artifact_blockers(run_request, main_skill, skills),
        *executable_contract_blockers(project, managed_runtime.runtimeCommand),
    ]
    if contract_blockers:
        result = {
            "schemaVersion": WORKFLOW_VALIDATION_READINESS_SCHEMA,
            "alias": alias,
            "status": "blocked",
            "selectedMainSkill": _selected_main_skill(record.mainSkill, main_skill),
            "managedRuntimeReadiness": managed_runtime.to_dict(),
            "blockers": [blocker.to_dict() for blocker in contract_blockers],
        }
        update_validation(project, alias, result)
        return result
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
                    recoveryCommand=f"proofsignal workflow persist implement --alias {alias} --payload <payload.json> --json",
                ).to_dict()
                for message in coherence.blockers
            ],
        }
        update_validation(project, alias, result)
        return result
    result = CoreAdapter(executable=managed_runtime.runtimeCommand, cwd=project).authoring_check(
        run_request,
        main_skill,
        skills,
        runtime_readiness=runtime_readiness,
        entitlement_receipt=_valid_receipt_path(),
    )
    runtime_check = evaluate_runtime_readiness(project, alias, authoring_result=result) if runtime_readiness else None
    wrapped = {
        "alias": alias,
        "status": result.get("status", "error"),
        "selectedMainSkill": _selected_main_skill(record.mainSkill, main_skill),
        "skillSelectionStatus": "matched",
        "authoringCoherence": coherence.to_dict(),
        "managedRuntimeReadiness": managed_runtime.to_dict(),
        "core": result,
    }
    entitlement_blocker_code = core_entitlement_blocker_code(result)
    if entitlement_blocker_code:
        blocker = RuntimeSetupBlocker(
            code=entitlement_blocker_code,
            message="ProofSignal Core rejected the entitlement receipt for this protected operation.",
            recoveryCommand="Run `proofsignal init --here --integration codex` to unlock or refresh runtime entitlement.",
        )
        wrapped["status"] = "blocked"
        wrapped["blockers"] = [ReadinessBlocker.from_dict(blocker.to_dict()).to_dict()]
    authored_evidence_status = _authored_evidence_coverage_status(coherence.to_dict().get("gateCoverage", []))
    runtime_status = "not-run"
    if runtime_check:
        wrapped["runtimeReadiness"] = runtime_check.to_dict()
        runtime_status = runtime_check.status
        if runtime_check.status != "passed":
            wrapped["status"] = "blocked"
            wrapped["blockers"] = [
                ReadinessBlocker(
                    code=finding,
                    message=runtime_check.message or "Runtime readiness is blocked.",
                    recoveryCommand=f"proofsignal workflow check validate --alias {alias} --json",
                ).to_dict()
                for finding in runtime_check.findingIds
            ]
    summary = ValidationReadinessSummary(
        alias=alias,
        status="blocked" if wrapped.get("status") == "blocked" else ("passed" if wrapped.get("status") == "passed" else "failed"),
        skillSelectionStatus="matched",
        authoringCoherenceStatus=coherence.status,
        authoredEvidenceCoverageStatus=authored_evidence_status,
        runtimeReadinessStatus=runtime_status,
        fullBrowserFlowExecuted=False,
        nextAction=f"proofsignal run {alias} --json" if wrapped.get("status") == "passed" else f"proofsignal workflow check validate --alias {alias} --json",
    )
    wrapped.update(summary.to_dict())
    wrapped["readinessSummary"] = _readiness_summary_text(summary)
    update_validation(project, alias, wrapped)
    guided_stage = None
    if summary.status == "passed":
        guided_stage = advance_guided_first_run_state(
            project,
            alias,
            stage="running",
            first_run_status="running",
            resume_command=f"proofsignal run {alias} --json",
            summary=f"{alias} validation readiness passed; the first browser run is ready.",
        )
    elif summary.status == "blocked":
        guided_stage = advance_guided_first_run_state(
            project,
            alias,
            stage="blocked",
            first_run_status="blocked",
            resume_command=summary.nextAction,
            summary=f"{alias} validation readiness is blocked.",
            status_marker="[BLOCKED]",
            blocker={"category": "validation-readiness", "requiredAction": summary.nextAction, "resumeCommand": summary.nextAction},
        )
    if guided_stage:
        wrapped["guidedFirstRunState"] = guided_stage
    return wrapped


def _authored_evidence_coverage_status(gate_coverage: list[dict[str, Any]]) -> str:
    if not gate_coverage:
        return "not-applicable"
    incomplete = {"missing", "network-only", "screenshot-only", "unmapped", "not-evaluated", "incomplete"}
    if any(item.get("required", True) and item.get("status") in incomplete for item in gate_coverage):
        return "incomplete"
    return "complete"


def _readiness_summary_text(summary: ValidationReadinessSummary) -> str:
    if summary.status == "passed":
        return (
            "Validation readiness passed: required gates have mapped authored evidence, "
            f"runtime readiness is {summary.runtimeReadinessStatus}, and the full browser flow has not executed yet. "
            f"Next action: {summary.nextAction}."
        )
    return (
        "Validation readiness did not pass. Review structural validation, authoring coherence, "
        "runtime readiness, and mapped authored evidence before running the browser flow."
    )


def _valid_receipt_path() -> str | None:
    receipt = load_receipt()
    if not receipt:
        return None
    status = receipt_status(receipt)
    return status.receiptPath if status.status == "valid" else None
