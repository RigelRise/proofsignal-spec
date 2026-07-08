from __future__ import annotations

from verifysignal_spec.workspace import layout
from verifysignal_spec.workspace.repository import init_workspace, load_document
from verifysignal_spec.workflows.engine import create_workflow_run, plan_artifacts


def test_workspace_contains_workflow_directories(tmp_path) -> None:
    init_workspace(tmp_path)
    assert layout.workflow_runs_dir(tmp_path).exists()
    assert layout.workflow_use_cases_dir(tmp_path).exists()
    assert layout.workflow_definition_path(tmp_path, "verifysignal-use-case").exists()


def test_understanding_global_and_snapshot_contract(tmp_path) -> None:
    init_workspace(tmp_path)
    create_workflow_run(tmp_path, "Validate login.", alias="login", integration="codex")
    assert layout.workflow_global_understanding_path(tmp_path).exists()
    assert layout.workflow_stage_document_path(tmp_path, "login", "understand").exists()
    state = load_document(layout.workflow_state_path(tmp_path, "login"))
    assert state["documents"]["understanding"] == ".verifysignal/workflows/use-cases/login/understanding.md"


def test_artifact_plan_has_one_run_request_and_reusable_skills(tmp_path) -> None:
    init_workspace(tmp_path)
    create_workflow_run(tmp_path, "Validate login.", alias="login", integration="codex")
    plan = plan_artifacts(tmp_path, "login")
    assert plan.runRequest == ".verifysignal/run-requests/login.yaml"
    assert isinstance(plan.supportingSkills, list)

