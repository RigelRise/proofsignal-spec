from __future__ import annotations

from proofsignal_spec.workspace.repository import init_workspace
from proofsignal_spec.workflows.engine import create_workflow_run, generate_tasks, plan_artifacts, specify
from proofsignal_spec.workflows.prerequisites import check_prerequisites


def test_clarify_missing_spec_points_to_specify(tmp_path) -> None:
    init_workspace(tmp_path)
    create_workflow_run(tmp_path, "Validate login.", alias="login", integration="codex")
    result = check_prerequisites(tmp_path, "clarify", alias="login")
    assert result["status"] == "missing"
    assert result["nextCommand"] == "/proofsignal-specify login"


def test_plan_missing_spec_points_to_specify(tmp_path) -> None:
    init_workspace(tmp_path)
    create_workflow_run(tmp_path, "Validate login.", alias="login", integration="codex")
    result = check_prerequisites(tmp_path, "plan", alias="login")
    assert result["status"] == "missing"
    assert result["nextCommand"] == "/proofsignal-specify login"


def test_tasks_missing_plan_points_to_plan(tmp_path) -> None:
    init_workspace(tmp_path)
    create_workflow_run(tmp_path, "Validate login.", alias="login", integration="codex")
    specify(tmp_path, "login", "Validate login.")
    result = check_prerequisites(tmp_path, "tasks", alias="login")
    assert result["status"] == "missing"
    assert result["nextCommand"] == "/proofsignal-plan login"


def test_implement_missing_tasks_points_to_tasks(tmp_path) -> None:
    init_workspace(tmp_path)
    create_workflow_run(tmp_path, "Validate login.", alias="login", integration="codex")
    specify(tmp_path, "login", "Validate login.")
    plan_artifacts(tmp_path, "login")
    result = check_prerequisites(tmp_path, "implement", alias="login")
    assert result["status"] == "missing"
    assert result["nextCommand"] == "/proofsignal-tasks login"


def test_validate_missing_generated_artifacts_points_to_implement(tmp_path) -> None:
    init_workspace(tmp_path)
    create_workflow_run(tmp_path, "Validate login.", alias="login", integration="codex")
    specify(tmp_path, "login", "Validate login.")
    plan_artifacts(tmp_path, "login")
    generate_tasks(tmp_path, "login")
    result = check_prerequisites(tmp_path, "validate", alias="login")
    assert result["status"] == "missing"
    assert result["nextCommand"] == "/proofsignal-implement login"
