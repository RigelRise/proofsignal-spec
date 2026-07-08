from __future__ import annotations

from pathlib import Path

from verifysignal_spec.workspace.repository import load_document

from .models import WORKFLOW_ID, WorkflowDefinition


def built_in_workflow_definition() -> WorkflowDefinition:
    return WorkflowDefinition(
        workflowId=WORKFLOW_ID,
        name="VerifySignal Use Case",
        version="1.0.0",
        gates=[
            {"gateId": "review-understanding", "stageBefore": "understand", "approve": "specify", "reject": "understand"},
            {"gateId": "review-spec", "stageBefore": "specify", "approve": "clarify", "reject": "specify"},
            {"gateId": "review-plan", "stageBefore": "plan", "approve": "tasks", "reject": "plan"},
            {"gateId": "review-tasks", "stageBefore": "tasks", "approve": "implement", "reject": "tasks"},
        ],
    )


def load_workflow_definition(project: Path, workflow_id: str = WORKFLOW_ID) -> WorkflowDefinition:
    if workflow_id != WORKFLOW_ID:
        raise ValueError(f"Unknown workflow: {workflow_id}")
    from verifysignal_spec.workspace import layout

    path = layout.workflow_definition_path(project, workflow_id)
    data = load_document(path)
    return WorkflowDefinition.from_dict(data) if data else built_in_workflow_definition()

