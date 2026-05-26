from __future__ import annotations

from proofsignal_spec.commands import run as run_command
from proofsignal_spec.commands import validate as validate_command
from proofsignal_spec.workflows.stage_persistence import persist_stage
from proofsignal_spec.workspace.repository import init_workspace, load_use_case

from tests.fixtures.workflows.real_run_guardrails import coherent_profile_skill, create_real_run_guardrail_workspace, run_request_payload


def test_validate_and_run_use_planned_main_skill_with_reusable_first(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    init_workspace(tmp_path, core_cmd=str(FAKE_CORE))
    create_real_run_guardrail_workspace(tmp_path)
    payload = {
        "runRequest": run_request_payload(skills_first=["skill.navigate-to-profile", "skill.validate-profile-view-unauth-flow"]),
        "skills": [
            coherent_profile_skill(".proofsignal/skills/navigate-to-profile.browser.md"),
            coherent_profile_skill(".proofsignal/skills/validate-profile-view-unauth-flow.browser.md"),
        ],
        "runtimeInputs": [{"name": "baseUrl", "default": "https://app.example.test", "source": "default"}],
    }
    persist_result = persist_stage(tmp_path, "implement", alias="profile-view-unauth", payload=payload)
    assert persist_result["status"] == "persisted"

    validation = validate_command.run(tmp_path, "profile-view-unauth", core_cmd=str(FAKE_CORE))
    run = run_command.run(tmp_path, "profile-view-unauth", core_cmd=str(FAKE_CORE), interactive=False)

    assert validation["selectedMainSkill"] == ".proofsignal/skills/validate-profile-view-unauth-flow.browser.md"
    assert run["selectedMainSkill"] == ".proofsignal/skills/validate-profile-view-unauth-flow.browser.md"
    record = load_use_case(tmp_path, "profile-view-unauth")
    assert record.lastRun
    assert record.lastRun["runId"] == "fake-run-1"
