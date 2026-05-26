from __future__ import annotations

from proofsignal_spec.commands import run as run_command
from proofsignal_spec.workflows.stage_persistence import persist_stage
from proofsignal_spec.workspace.repository import init_workspace, load_use_case

from tests.fixtures.workflows.real_run_guardrails import coherent_profile_skill, create_real_run_guardrail_workspace, run_request_payload


def test_custom_profile_is_persisted_and_passed_to_core(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    init_workspace(tmp_path, core_cmd=str(FAKE_CORE))
    create_real_run_guardrail_workspace(tmp_path)
    result = persist_stage(
        tmp_path,
        "implement",
        alias="profile-view-unauth",
        payload={
            "runRequest": run_request_payload(),
            "skills": [coherent_profile_skill()],
            "profiles": [
                {"name": "normal", "headed": False, "slowMoMs": 0},
                {"name": "debug", "headed": True, "slowMoMs": 700},
                {"name": "visual-15s", "headed": True, "slowMoMs": 15000},
            ],
        },
    )
    assert result["status"] == "persisted"

    run = run_command.run(tmp_path, "profile-view-unauth", profile_name="visual-15s", core_cmd=str(FAKE_CORE), interactive=False)

    assert run["profileSettings"] == {"headed": True, "slowMoMs": 15000}
    assert run["core"]["data"]["headed"] is True
    assert run["core"]["data"]["slowMoMs"] == 15000
    record = load_use_case(tmp_path, "profile-view-unauth")
    assert record.lastRun
    assert record.lastRun["profile"] == "visual-15s"


def test_unknown_profile_lists_available_profiles(tmp_path) -> None:
    create_real_run_guardrail_workspace(tmp_path)

    try:
        run_command.run(tmp_path, "profile-view-unauth", profile_name="visual", interactive=False)
    except ValueError as exc:
        message = str(exc)
    else:  # pragma: no cover
        raise AssertionError("unknown profile should fail")

    assert "Unknown profile for profile-view-unauth: visual" in message
    assert "normal" in message
