from __future__ import annotations

from proofsignal_spec.workspace.repository import create_default_use_case, init_workspace, load_use_case, save_use_case
from proofsignal_spec.workflows.repository import import_legacy_use_case


def test_legacy_use_case_imports_as_workflow_draft(tmp_path) -> None:
    init_workspace(tmp_path)
    save_use_case(tmp_path, create_default_use_case(tmp_path, "login", "Validate login."))
    result = import_legacy_use_case(tmp_path, "login")
    assert result["alias"] == "login"
    assert load_use_case(tmp_path, "login").workflow is not None

