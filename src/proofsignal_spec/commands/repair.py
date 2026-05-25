from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.core.adapter import CoreAdapter
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
        findings = list(record.validation.get("data", {}).get("findings", record.validation.get("findings", [])))
    proposals = [
        {
            "artifact": finding.get("artifact") or (record.runRequest.path if record.runRequest else f".proofsignal/use-cases/{alias}.yaml"),
            "field": finding.get("path"),
            "reason": finding.get("message", "Core finding requires review."),
            "expectedEffect": finding.get("suggestedFix", "Update the artifact and revalidate."),
        }
        for finding in findings
    ] or [
        {
            "artifact": record.runRequest.path if record.runRequest else f".proofsignal/use-cases/{alias}.yaml",
            "field": None,
            "reason": "No deterministic finding was available.",
            "expectedEffect": "Review the use case and run validation again.",
        }
    ]
    session = RepairSession(
        repairId=f"{alias}-{now_iso().replace(':', '').replace('-', '')}",
        useCaseAlias=alias,
        source=source,
        findings=findings,
        proposals=proposals,
        approvalStatus="approved" if approve else "pending",
    )
    if approve:
        session.approvalStatus = "applied"
        session.appliedAt = now_iso()
    record.repair = {"repairId": session.repairId, "approvalStatus": session.approvalStatus}
    save_use_case(project, record)
    save_document(layout.repair_path(project, session.repairId), session.to_dict())
    return {"alias": alias, "repair": session.to_dict()}
