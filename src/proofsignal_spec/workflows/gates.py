from __future__ import annotations

from .models import WorkflowGateDecision, WorkflowRun


def latest_gate_decision(run: WorkflowRun, gate_id: str) -> WorkflowGateDecision | None:
    for decision in reversed(run.gateDecisions):
        if decision.gateId == gate_id:
            return decision
    return None


def gate_is_approved(run: WorkflowRun, gate_id: str) -> bool:
    decision = latest_gate_decision(run, gate_id)
    return bool(decision and decision.decision == "approved")


def blocker(code: str, message: str, path: str | None = None) -> dict[str, str]:
    result = {"code": code, "message": message}
    if path:
        result["path"] = path
    return result
