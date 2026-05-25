from __future__ import annotations

from proofsignal_spec.workflows.models import ArtifactPlan, WorkflowRun, WorkflowStageState, native_invocation


def test_workflow_run_round_trips_structured_state() -> None:
    run = WorkflowRun(runId="wf-1", useCaseAlias="login", stageStates=[WorkflowStageState(stage="understand", status="completed")])
    data = run.to_dict()
    assert data["schemaVersion"] == "proofsignal-spec-workflow-run/v1"
    assert WorkflowRun.from_dict(data).stageStates[0].status == "completed"


def test_artifact_plan_requires_single_run_request_reference() -> None:
    plan = ArtifactPlan(useCaseAlias="login", runRequest=".proofsignal/run-requests/login.yaml", mainSkill=".proofsignal/skills/login.browser.md")
    assert plan.to_dict()["runRequest"] == ".proofsignal/run-requests/login.yaml"
    assert native_invocation("plan") == "/proofsignal-plan"

