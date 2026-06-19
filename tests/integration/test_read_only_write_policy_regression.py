from __future__ import annotations

from proofsignal_spec.workspace.models import ArtifactReference, UseCaseRecord
from proofsignal_spec.workspace.repository import init_workspace, save_use_case
from proofsignal_spec.workspace.validation import validate_use_case


def test_read_only_alias_is_unaffected_by_write_policy_compatibility_checks(tmp_path) -> None:
    init_workspace(tmp_path)
    (tmp_path / ".proofsignal/run-requests").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".proofsignal/skills").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".proofsignal/run-requests/about.yaml").write_text("{}", encoding="utf-8")
    (tmp_path / ".proofsignal/skills/about.browser.md").write_text("# About\n", encoding="utf-8")
    record = UseCaseRecord(
        alias="about-page-unauth",
        title="About",
        description="Read-only about page.",
        runRequest=ArtifactReference(path=".proofsignal/run-requests/about.yaml", kind="run-request"),
        mainSkill=ArtifactReference(path=".proofsignal/skills/about.browser.md", kind="skill"),
        skills=[ArtifactReference(path=".proofsignal/skills/about.browser.md", kind="skill")],
        sideEffects={"class": "none"},
    )
    save_use_case(tmp_path, record)

    findings = validate_use_case(tmp_path, record)

    assert not [item for item in findings if item["severity"] == "blocking"]
