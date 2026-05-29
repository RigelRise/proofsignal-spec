from __future__ import annotations

from .models import GateIntentState, WorkflowGateDecision, WorkflowRun


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


def gate_intent_from_plan(gate: dict[str, object]) -> GateIntentState:
    required = bool(gate.get("required", True))
    condition = str(gate.get("condition") or "").strip() or None
    return GateIntentState(
        gateId=str(gate.get("id") or gate.get("gateId") or ""),
        required=required,
        condition=condition,
        conditionStatus="unknown" if condition else "not-applicable",
        changeSource="plan",
        changeReason=str(gate.get("description") or "Gate intent recorded from artifact plan."),
    )


def preserve_required_after_aborted_run(state: GateIntentState, *, source_run_id: str) -> GateIntentState:
    return GateIntentState(
        gateId=state.gateId,
        required=state.required,
        condition=state.condition,
        conditionStatus=state.conditionStatus,
        changeSource=state.changeSource,
        changeReason=f"{state.changeReason} Requiredness preserved after aborted run {source_run_id}.",
    )


def record_gate_intent_change(
    state: GateIntentState,
    *,
    required: bool,
    source: str,
    reason: str,
    condition: str | None = None,
) -> GateIntentState:
    return GateIntentState(
        gateId=state.gateId,
        required=required,
        condition=condition,
        conditionStatus="unknown" if condition else "not-applicable",
        changeSource=source,  # type: ignore[arg-type]
        changeReason=reason,
    )
