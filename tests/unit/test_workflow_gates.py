from __future__ import annotations

from proofsignal_spec.workflows.gates import gate_is_approved
from proofsignal_spec.workflows.models import WorkflowGateDecision, WorkflowRun


def test_gate_approval_uses_latest_decision() -> None:
    run = WorkflowRun(
        runId="wf-1",
        gateDecisions=[
            WorkflowGateDecision("review-plan", "plan", "rejected", "2026-05-25T00:00:00Z"),
            WorkflowGateDecision("review-plan", "plan", "approved", "2026-05-25T00:01:00Z"),
        ],
    )
    assert gate_is_approved(run, "review-plan")
