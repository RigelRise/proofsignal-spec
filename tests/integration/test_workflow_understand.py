from __future__ import annotations

from proofsignal_spec.workspace.repository import init_workspace
from proofsignal_spec.workflows.engine import create_workflow_run


def test_understand_creates_global_context_and_snapshot(tmp_path) -> None:
    init_workspace(tmp_path)
    run = create_workflow_run(tmp_path, "Validate login.", alias="login", integration="codex")
    assert run.currentStage == "understand"
    assert (tmp_path / ".proofsignal" / "workflows" / "understanding.md").exists()
    assert (tmp_path / ".proofsignal" / "workflows" / "use-cases" / "login" / "understanding.md").exists()

