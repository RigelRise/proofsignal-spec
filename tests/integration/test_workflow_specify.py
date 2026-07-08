from __future__ import annotations

from verifysignal_spec.workspace.repository import init_workspace
from verifysignal_spec.workflows.engine import create_workflow_run, specify


def test_specify_writes_use_case_spec(tmp_path) -> None:
    init_workspace(tmp_path)
    create_workflow_run(tmp_path, "Validate login.", alias="login", integration="codex")
    result = specify(tmp_path, "login", "Validate login.")
    assert result["documentPath"] == ".verifysignal/workflows/use-cases/login/spec.md"
    assert (tmp_path / result["documentPath"]).exists()

