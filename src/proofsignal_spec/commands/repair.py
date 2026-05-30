from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.core.adapter import CoreAdapter
from proofsignal_spec.workflows.models import RepairConfirmation, RepairFeedback, SafeRepairApplication
from proofsignal_spec.workflows.repair_recommendations import classify_repair_findings, proposals_from_contradictions
from proofsignal_spec.workflows.repository import load_golden_path_state, save_golden_path_state
from proofsignal_spec.workflows.stage_cards import repair_stage_card
from proofsignal_spec.workspace import layout
from proofsignal_spec.workspace.models import RepairSession
from proofsignal_spec.workspace.repository import get_core_command, load_use_case, now_iso, save_document, save_use_case


def run(project: Path, alias: str, from_report: str | None = None, approve: bool = False, core_cmd: str | None = None) -> dict[str, Any]:
    record = load_use_case(project, alias)
    source = "report-inspection" if from_report else "authoring-validation"
    findings: list[dict[str, Any]]
    if from_report:
        result = CoreAdapter(executable=core_cmd or get_core_command(project), cwd=project).inspect_report(Path(from_report))
        findings = list(result.get("data", {}).get("findings", []))
    else:
        findings = list(
            record.validation.get("data", {}).get(
                "findings",
                record.validation.get("findings", record.validation.get("core", {}).get("data", {}).get("findings", [])),
            )
        )
    contradictions = []
    if record.lastRun and isinstance(record.lastRun.get("runtimeContradictions"), list):
        contradictions = list(record.lastRun.get("runtimeContradictions") or [])
        findings.extend(
            {
                "severity": "warning",
                "code": "runtime-contradiction",
                "artifact": ".proofsignal/workflows",
                "path": item.get("gateId"),
                "message": item.get("observedEvidence", "Runtime evidence contradicted the planned gate."),
                "suggestedFix": item.get("recommendation", "replan"),
            }
            for item in contradictions
        )
    proposals = [
        {
            "artifact": finding.get("artifact") or (record.runRequest.path if record.runRequest else f".proofsignal/use-cases/{alias}.yaml"),
            "field": finding.get("path"),
            "reason": finding.get("message", "Core finding requires review."),
            "expectedEffect": finding.get("suggestedFix", "Update the artifact and revalidate."),
        }
        for finding in findings
    ]
    if contradictions:
        from proofsignal_spec.workflows.models import RuntimeContradiction

        proposals.extend(
            proposals_from_contradictions(
                [
                    RuntimeContradiction(
                        id=str(item.get("id", "")),
                        gateId=str(item.get("gateId", "")),
                        observedEvidence=str(item.get("observedEvidence", "")),
                        expectedEvidence=str(item.get("expectedEvidence", "")),
                        recommendation=item.get("recommendation", "replan"),
                        sourceRunId=item.get("sourceRunId"),
                    )
                    for item in contradictions
                ]
            )
        )
    proposals = proposals or [
        {
            "artifact": record.runRequest.path if record.runRequest else f".proofsignal/use-cases/{alias}.yaml",
            "field": None,
            "reason": "No deterministic finding was available.",
            "expectedEffect": "Review the use case and run validation again.",
        }
    ]
    recommendations = classify_repair_findings(findings)
    if not recommendations and proposals:
        recommendations = classify_repair_findings(
            [
                {
                    "code": proposal.get("field") or "manual-review",
                    "message": f"{proposal.get('reason', '')} {proposal.get('expectedEffect', '')}",
                    "artifact": proposal.get("artifact"),
                    "path": proposal.get("field"),
                }
                for proposal in proposals
            ]
        )
    auto_applicable = [item for item in recommendations if item.category == "safe-artifact-repair" and not item.requiresUserDecision]
    blocked = [
        item
        for item in recommendations
        if item.category in {"clarification-required", "replan-required", "unsupported"}
        or item.requiresUserDecision
    ]
    applications = [
        SafeRepairApplication(
            recommendationId=item.id,
            applied=item in auto_applicable and not blocked,
            changedArtifacts=item.affectedArtifacts,
            validationStatus="not-run",
            remainingGaps=[] if item in auto_applicable and not blocked else [item.id],
        ).to_dict()
        for item in recommendations
        if item.category == "safe-artifact-repair"
    ]
    repair_confirmations = [
        RepairConfirmation(
            id=f"confirm-{item.id}",
            findingId=(item.sourceFeedback[0] if item.sourceFeedback else item.id),
            category=item.runtimeCategory or item.safeCategory or item.category,
            confirmationSource="explicit-command",
            confirmationTextSummary="Repair was explicitly approved, but the change still requires scoped artifact work and revalidation.",
            approvedScope=item.affectedArtifacts or [item.action],
            affectedArtifacts=item.affectedArtifacts,
            revalidationRequired=True,
            status="pending",
        ).to_dict()
        for item in recommendations
        if approve and item.requiresUserDecision
    ]
    repair_feedback = [
        RepairFeedback(
            repairId=item.id,
            category=item.runtimeCategory or item.safeCategory or item.category,
            autonomy=item.autonomy,
            safeMechanical=item.safeMechanical,
            before=item.summary or "Runtime feedback identified a repairable issue.",
            after=item.action if item.autonomy == "auto-applied" else None,
            intentPreserved=item.intentPreserved,
            confirmationRequired=item.requiresUserDecision,
            revalidationStatus="not-run",
            rerunStatus="not-run",
            nextAction=f"Run `proofsignal-spec validate {alias} --runtime-readiness --json`, then rerun.",
        ).to_dict()
        for item in recommendations
    ]
    stage_cards = [
        repair_stage_card(
            category=item.runtimeCategory or item.safeCategory or item.category,
            autonomy=item.autonomy,
            before=item.summary or "Runtime feedback identified a repairable issue.",
            after=item.action if item.autonomy == "auto-applied" else item.blockedReason or item.action,
            next_action=f"Run `proofsignal-spec validate {alias} --runtime-readiness --json`, then rerun.",
        )
        for item in recommendations
        if item.autonomy == "auto-applied"
    ]
    session = RepairSession(
        repairId=f"{alias}-{now_iso().replace(':', '').replace('-', '')}",
        useCaseAlias=alias,
        source=source,
        findings=findings,
        proposals=proposals,
        recommendations=[item.to_dict() for item in recommendations],
        repairConfirmations=repair_confirmations,
        applications=applications,
        repairFeedback=repair_feedback,
        stageCards=stage_cards,
        approvalStatus="applied" if auto_applicable and not blocked else ("conflict" if approve and blocked else ("approved" if approve else "pending")),
        nextAction=f"Run `proofsignal-spec validate {alias} --runtime-readiness --json`, then rerun.",
    )
    if auto_applicable and not blocked:
        session.appliedAt = now_iso()
        session.revalidation = {
            "status": "not-run",
            "message": "Safe mechanical repair was auto-applied; revalidation and rerun are required before reporting success.",
        }
        session.readyForRun = False
    elif blocked:
        session.readyForRun = False
        session.revalidation = {
            "status": "not-run",
            "message": "Repair changes approved intent or is unsupported; return to clarification or planning.",
        }
    record.repair = {"repairId": session.repairId, "approvalStatus": session.approvalStatus}
    save_use_case(project, record)
    save_document(layout.repair_path(project, session.repairId), session.to_dict())
    _update_first_run_repair_state(project, alias, repair_feedback, session.approvalStatus)
    return {"alias": alias, "repair": session.to_dict()}


def _update_first_run_repair_state(project: Path, alias: str, repair_feedback: list[dict[str, Any]], approval_status: str) -> None:
    state = load_golden_path_state(project)
    if state.get("selectedCandidate") != alias:
        return
    state["repairFeedback"] = repair_feedback
    if approval_status == "applied":
        state["firstRunStatus"] = "repairing"
    save_golden_path_state(project, state)
