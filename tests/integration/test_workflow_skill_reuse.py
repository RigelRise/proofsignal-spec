from __future__ import annotations

from verifysignal_spec.workspace.models import ArtifactReference
from verifysignal_spec.workspace.repository import create_default_use_case, init_workspace, save_use_case
from verifysignal_spec.workflows.repository import index_skill_reuse


def test_shared_skill_index_reports_affected_use_cases(tmp_path) -> None:
    init_workspace(tmp_path)
    for alias in ["login", "checkout"]:
        record = create_default_use_case(tmp_path, alias, f"Validate {alias}.")
        record.skills = [ArtifactReference(path=".verifysignal/skills/login.browser.md", kind="skill")]
        save_use_case(tmp_path, record)
    index = index_skill_reuse(tmp_path)
    assert len(index[".verifysignal/skills/login.browser.md"]) == 2


def test_shared_skill_index_includes_source_only_skill_metadata(tmp_path) -> None:
    init_workspace(tmp_path)
    record = create_default_use_case(tmp_path, "brands-search", "Validate authenticated brands search.")
    record.skills = [ArtifactReference(path=".verifysignal/skills/main.browser.md", kind="skill")]
    record.sourceOnlySkills = [ArtifactReference(path=".verifysignal/skills/login.browser.md", kind="skill")]
    save_use_case(tmp_path, record)

    index = index_skill_reuse(tmp_path)

    assert index[".verifysignal/skills/login.browser.md"] == [
        {"useCaseAlias": "brands-search", "runRequest": ".verifysignal/run-requests/brands-search.yaml"}
    ]
