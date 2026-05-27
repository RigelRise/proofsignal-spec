from __future__ import annotations

from proofsignal_spec.workspace.repository import init_workspace, load_use_case
from proofsignal_spec.workflows.engine import create_workflow_run, generate_tasks, implement_artifacts, plan_artifacts, validate_stage
from tests.fixtures.workflows.main_skill_run_coverage import create_main_skill_coverage_workspace


def test_implement_creates_draft_artifacts(tmp_path) -> None:
    init_workspace(tmp_path)
    create_workflow_run(tmp_path, "Validate login.", alias="login", integration="codex")
    plan_artifacts(tmp_path, "login")
    generate_tasks(tmp_path, "login")
    result = implement_artifacts(tmp_path, "login")
    assert result["status"] == "draft"
    assert (tmp_path / ".proofsignal" / "run-requests" / "login.yaml").exists()
    assert load_use_case(tmp_path, "login").status == "draft"


def test_implemented_browser_artifacts_require_runtime_readiness_validation(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    create_main_skill_coverage_workspace(tmp_path)

    result = validate_stage(tmp_path, "profile-view-unauth", core_cmd=str(FAKE_CORE))

    assert result["status"] == "passed"
    assert result["runtimeReadiness"]["status"] == "passed"
    assert result["runtimeReadiness"]["fullBrowserFlowExecuted"] is False
