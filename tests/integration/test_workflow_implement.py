from __future__ import annotations

from proofsignal_spec.workspace.repository import init_workspace, load_use_case
from proofsignal_spec.workflows.engine import create_workflow_run, generate_tasks, implement_artifacts, plan_artifacts


def test_implement_creates_draft_artifacts(tmp_path) -> None:
    init_workspace(tmp_path)
    create_workflow_run(tmp_path, "Validate login.", alias="login", integration="codex")
    plan_artifacts(tmp_path, "login")
    generate_tasks(tmp_path, "login")
    result = implement_artifacts(tmp_path, "login")
    assert result["status"] == "draft"
    assert (tmp_path / ".proofsignal" / "run-requests" / "login.yaml").exists()
    assert load_use_case(tmp_path, "login").status == "draft"

