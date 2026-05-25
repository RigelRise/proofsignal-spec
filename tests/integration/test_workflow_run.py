from __future__ import annotations

from proofsignal_spec.workspace.repository import init_workspace
from proofsignal_spec.workflows.engine import create_workflow_run, generate_tasks, implement_artifacts, plan_artifacts, validate_stage


def test_workflow_validate_preserves_core_result(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    init_workspace(tmp_path, core_cmd=str(FAKE_CORE))
    create_workflow_run(tmp_path, "Validate login.", alias="login", integration="codex")
    plan_artifacts(tmp_path, "login")
    generate_tasks(tmp_path, "login")
    implement_artifacts(tmp_path, "login")
    result = validate_stage(tmp_path, "login")
    assert result["core"]["schemaVersion"]

