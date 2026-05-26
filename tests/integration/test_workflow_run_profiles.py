from __future__ import annotations

from proofsignal_spec.cli import main
from proofsignal_spec.workflows.stage_persistence import persist_stage
from proofsignal_spec.workspace.repository import init_workspace

from tests.fixtures.workflows.real_run_guardrails import coherent_profile_skill, create_real_run_guardrail_workspace, run_request_payload


def test_cli_runs_custom_visual_profile_for_one_use_case(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    init_workspace(tmp_path, core_cmd=str(FAKE_CORE))
    create_real_run_guardrail_workspace(tmp_path)
    persist_stage(
        tmp_path,
        "implement",
        alias="profile-view-unauth",
        payload={
            "runRequest": run_request_payload(),
            "skills": [coherent_profile_skill()],
            "profiles": [
                {"name": "normal", "headed": False, "slowMoMs": 0},
                {"name": "visual-15s", "headed": True, "slowMoMs": 15000},
            ],
        },
    )

    code = main(["run", "profile-view-unauth", "--project", str(tmp_path), "--profile", "visual-15s", "--non-interactive", "--json"])

    assert code == 0


def test_cli_blocks_unknown_custom_profile(tmp_path) -> None:
    create_real_run_guardrail_workspace(tmp_path)

    code = main(["run", "profile-view-unauth", "--project", str(tmp_path), "--profile", "visual", "--non-interactive"])

    assert code != 0
