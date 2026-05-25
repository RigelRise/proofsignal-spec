from __future__ import annotations

from proofsignal_spec.workspace.repository import init_workspace
from proofsignal_spec.workflows.engine import clarify, create_workflow_run


def test_clarify_writes_questions(tmp_path) -> None:
    init_workspace(tmp_path)
    create_workflow_run(tmp_path, "Validate login.", alias="login", integration="codex")
    result = clarify(tmp_path, "login")
    assert result["questions"]
    assert (tmp_path / ".proofsignal" / "workflows" / "use-cases" / "login" / "clarifications.md").exists()

