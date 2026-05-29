from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.core.adapter import CoreAdapter
from proofsignal_spec.core.contracts import public_contract_summary
from proofsignal_spec.core.errors import CoreExecutionError, CoreIncompatibleError, CoreMissingError
from proofsignal_spec.workspace import layout
from proofsignal_spec.workspace.repository import get_core_command
from proofsignal_spec.workspace.validation import validate_use_case, validate_workspace

from .migration import migration_plans
from .models import (
    WORKFLOW_CAPABILITY_SCHEMA,
    WORKFLOW_GUARDRAILS_CAPABILITY,
    WORKFLOW_VALIDATION_READINESS_SCHEMA,
    CoreReadiness,
    ReadinessBlocker,
    StructuralWorkspaceValidation,
)


def validation_readiness(project: Path, alias: str | None = None, core_cmd: str | None = None) -> dict[str, Any]:
    structural = structural_validation(project, alias=alias)
    core = core_readiness(project, core_cmd=core_cmd)
    blockers = _blockers(structural, core)
    status = _overall_status(structural, core)
    return {
        "schemaVersion": WORKFLOW_VALIDATION_READINESS_SCHEMA,
        "capabilitySchemaVersion": WORKFLOW_CAPABILITY_SCHEMA,
        "requiredCapability": WORKFLOW_GUARDRAILS_CAPABILITY,
        "supported": True,
        "stage": "validate",
        "alias": alias,
        "status": status,
        "structuralValidation": structural.to_dict(),
        "coreReadiness": core.to_dict(),
        "blockers": [blocker.to_dict() for blocker in blockers],
    }


def structural_validation(project: Path, alias: str | None = None) -> StructuralWorkspaceValidation:
    findings = validate_workspace(project)
    checked = [f"{layout.WORKSPACE_DIR}/{layout.REGISTRY_FILE}"]
    if alias:
        checked.append(f"{layout.WORKSPACE_DIR}/{layout.USE_CASES_DIR}/{alias}.yaml")
        try:
            from proofsignal_spec.workspace.repository import load_use_case

            record = load_use_case(project, alias)
            findings.extend(validate_use_case(project, record))
            if record.runRequest:
                checked.append(record.runRequest.path)
            checked.extend(skill.path for skill in record.skills)
        except Exception as exc:
            findings.append(
                {
                    "severity": "blocking",
                    "code": "missing-or-invalid-use-case-record",
                    "path": f"{layout.WORKSPACE_DIR}/{layout.USE_CASES_DIR}/{alias}.yaml",
                    "message": str(exc),
                }
            )
    plans = migration_plans(project, alias=alias)
    if plans:
        findings.append(
            {
                "severity": "blocking",
                "code": "migration-required",
                "path": f"{layout.WORKSPACE_DIR}/{layout.REGISTRY_FILE}",
                "message": "Recoverable malformed workspace artifacts require approved migration before validation.",
            }
        )
    if any(item.get("severity") == "blocking" for item in findings):
        status = "blocked"
    elif findings:
        status = "warning"
    else:
        status = "pass"
    return StructuralWorkspaceValidation(status=status, findings=findings, checkedArtifacts=checked, migrationPlans=plans)


def core_readiness(project: Path, core_cmd: str | None = None) -> CoreReadiness:
    configured = core_cmd or get_core_command(project)
    contract = public_contract_summary()
    try:
        adapter = CoreAdapter(executable=configured, cwd=project)
        compatible = adapter.check_compatibility()
        if not compatible.compatible:
            return CoreReadiness(
                status="incompatible",
                coreCommand=adapter.executable,
                version=compatible.proofsignalVersion,
                contractVersion=compatible.contractVersion or contract["contractVersion"],
                requiredOperations=contract["requiredOperations"],
                missingOperations=compatible.missingOperations or [],
                incompatibleOperations=compatible.incompatibleOperations or [],
                recoveryAction=compatible.recoveryAction,
                message=compatible.message,
            )
        return CoreReadiness(
            status="available",
            coreCommand=adapter.executable,
            version=compatible.proofsignalVersion,
            contractVersion=compatible.contractVersion or contract["contractVersion"],
            requiredOperations=contract["requiredOperations"],
            missingOperations=[],
            message="ProofSignal Core is available for complete validation and browser execution.",
        )
    except CoreMissingError as exc:
        return CoreReadiness(
            status="missing",
            coreCommand=configured,
            contractVersion=contract["contractVersion"],
            requiredOperations=contract["requiredOperations"],
            message=f"{exc} Structural workspace validation can still run, but ProofSignal Core is required for the complete ProofSignal validation and browser execution experience.",
        )
    except CoreIncompatibleError as exc:
        return CoreReadiness(status="incompatible", coreCommand=configured, requiredOperations=contract["requiredOperations"], message=str(exc))
    except CoreExecutionError as exc:
        return CoreReadiness(status="error", coreCommand=configured, requiredOperations=contract["requiredOperations"], message=str(exc))
    except Exception as exc:
        return CoreReadiness(status="error", coreCommand=configured, requiredOperations=contract["requiredOperations"], message=str(exc))


def _blockers(structural: StructuralWorkspaceValidation, core: CoreReadiness) -> list[ReadinessBlocker]:
    blockers: list[ReadinessBlocker] = []
    if structural.status == "blocked":
        blockers.append(
            ReadinessBlocker(
                code="workspace.structural-blocked",
                message="Workspace structure is blocked. Review structuralValidation.findings and apply approved migrations when offered.",
                recoveryCommand="proofsignal-spec workflow check validate --json",
            )
        )
    if core.status == "missing":
        blockers.append(
            ReadinessBlocker(
                code="core.missing",
                message="ProofSignal Core is required for complete validation and browser execution.",
                recoveryCommand="proofsignal-spec init --core-cmd /path/to/proofsignal",
            )
        )
    elif core.status == "incompatible":
        blockers.append(
            ReadinessBlocker(
                code="core.incompatible",
                message=core.message or "ProofSignal Core is incompatible with the required public contract.",
                recoveryCommand="proofsignal-spec core version --json",
            )
        )
    elif core.status == "error":
        blockers.append(ReadinessBlocker(code="core.error", message=core.message or "ProofSignal Core failed readiness check."))
    return blockers


def _overall_status(structural: StructuralWorkspaceValidation, core: CoreReadiness) -> str:
    if structural.status == "blocked":
        return "blocked"
    if core.status == "available":
        return "ready" if structural.status == "pass" else "warning"
    if structural.status == "pass":
        return "blocked"
    return "blocked"
