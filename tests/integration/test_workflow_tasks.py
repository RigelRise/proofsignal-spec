from __future__ import annotations

from verifysignal_spec.workspace.repository import init_workspace
from verifysignal_spec.workflows.engine import create_workflow_run, generate_tasks, plan_artifacts


def test_workflow_tasks_trace_to_plan(tmp_path) -> None:
    init_workspace(tmp_path)
    create_workflow_run(tmp_path, "Validate login.", alias="login", integration="codex")
    plan_artifacts(tmp_path, "login")
    result = generate_tasks(tmp_path, "login")
    assert result["tasks"]
    assert result["sourcePlanPath"].endswith("/plan.md")

