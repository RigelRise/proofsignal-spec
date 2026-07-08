from __future__ import annotations

from verifysignal_spec.commands import run as run_command
from verifysignal_spec.commands import validate as validate_command
from verifysignal_spec.workspace.repository import load_use_case, save_use_case
from tests.fixtures.workflows.main_skill_run_coverage import HELPER_SKILL_PATH, MAIN_SKILL_ID, MAIN_SKILL_PATH, create_main_skill_coverage_workspace


def test_helper_first_workspace_invokes_only_planned_main_skill_when_multi_skill_unsupported(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("VERIFYSIGNAL_CORE_CMD", str(FAKE_CORE))
    monkeypatch.setenv("FAKE_VERIFYSIGNAL_MODE", "full-coverage")
    create_main_skill_coverage_workspace(tmp_path, helper_first=True)

    result = run_command.run(tmp_path, "profile-view-unauth", interactive=False, core_cmd=str(FAKE_CORE))
    skill_flags = [
        result["core"]["data"]["args"][index + 1]
        for index, item in enumerate(result["core"]["data"]["args"])
        if item == "--skill"
    ]

    assert len(skill_flags) == 1
    assert skill_flags[0].endswith(MAIN_SKILL_PATH)
    assert result["selectedMainSkill"]["id"] == MAIN_SKILL_ID
    assert result["skillSelectionStatus"] == "matched"


def test_validate_summary_includes_selected_main_skill(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("VERIFYSIGNAL_CORE_CMD", str(FAKE_CORE))
    create_main_skill_coverage_workspace(tmp_path, helper_first=True)

    result = validate_command.run(tmp_path, "profile-view-unauth", core_cmd=str(FAKE_CORE))

    assert result["status"] == "passed"
    assert result["selectedMainSkill"]["path"] == MAIN_SKILL_PATH
    record = load_use_case(tmp_path, "profile-view-unauth")
    assert record.mainSkill and record.mainSkill.path == MAIN_SKILL_PATH


def test_core_declared_multi_skill_support_allows_additional_participants(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("VERIFYSIGNAL_CORE_CMD", str(FAKE_CORE))
    monkeypatch.setenv("FAKE_VERIFYSIGNAL_MODE", "multi-skill-supported")
    create_main_skill_coverage_workspace(tmp_path, helper_first=True)
    record = load_use_case(tmp_path, "profile-view-unauth")
    record.sourceOnlySkills = []
    save_use_case(tmp_path, record)

    result = run_command.run(tmp_path, "profile-view-unauth", interactive=False, core_cmd=str(FAKE_CORE))
    skill_flags = [
        result["core"]["data"]["args"][index + 1]
        for index, item in enumerate(result["core"]["data"]["args"])
        if item == "--skill"
    ]

    assert skill_flags[0].endswith(MAIN_SKILL_PATH)
    assert any(item.endswith(HELPER_SKILL_PATH) for item in skill_flags[1:])
