from __future__ import annotations

from proofsignal_spec.commands import run as run_command
from proofsignal_spec.commands import validate as validate_command
from proofsignal_spec.workspace.repository import load_use_case
from tests.fixtures.workflows.main_skill_run_coverage import (
    HELPER_SKILL_PATH,
    MAIN_SKILL_ID,
    MAIN_SKILL_PATH,
    create_main_skill_coverage_workspace,
)


def test_helper_first_workspace_still_invokes_planned_main_skill_first(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    monkeypatch.setenv("FAKE_PROOFSIGNAL_MODE", "full-coverage")
    create_main_skill_coverage_workspace(tmp_path, helper_first=True)

    result = run_command.run(tmp_path, "profile-view-unauth", interactive=False, core_cmd=str(FAKE_CORE))
    skill_flags = [
        result["core"]["data"]["args"][index + 1]
        for index, item in enumerate(result["core"]["data"]["args"])
        if item == "--skill"
    ]

    assert skill_flags[0].endswith(MAIN_SKILL_PATH)
    assert any(item.endswith(HELPER_SKILL_PATH) for item in skill_flags[1:])
    assert result["selectedMainSkill"]["id"] == MAIN_SKILL_ID
    assert result["skillSelectionStatus"] == "matched"


def test_validate_summary_includes_selected_main_skill(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    create_main_skill_coverage_workspace(tmp_path, helper_first=True)

    result = validate_command.run(tmp_path, "profile-view-unauth", core_cmd=str(FAKE_CORE))

    assert result["status"] == "passed"
    assert result["selectedMainSkill"]["path"] == MAIN_SKILL_PATH
    record = load_use_case(tmp_path, "profile-view-unauth")
    assert record.mainSkill and record.mainSkill.path == MAIN_SKILL_PATH
