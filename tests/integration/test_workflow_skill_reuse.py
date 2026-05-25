from __future__ import annotations

from proofsignal_spec.workspace.models import ArtifactReference
from proofsignal_spec.workspace.repository import create_default_use_case, init_workspace, save_use_case
from proofsignal_spec.workflows.repository import index_skill_reuse


def test_shared_skill_index_reports_affected_use_cases(tmp_path) -> None:
    init_workspace(tmp_path)
    for alias in ["login", "checkout"]:
        record = create_default_use_case(tmp_path, alias, f"Validate {alias}.")
        record.skills = [ArtifactReference(path=".proofsignal/skills/login.browser.md", kind="skill")]
        save_use_case(tmp_path, record)
    index = index_skill_reuse(tmp_path)
    assert len(index[".proofsignal/skills/login.browser.md"]) == 2

