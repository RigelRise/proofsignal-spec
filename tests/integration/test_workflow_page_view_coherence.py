from __future__ import annotations

from verifysignal_spec.workflows.stage_persistence import persist_stage

from tests.fixtures.workflows.real_run_guardrails import (
    coherent_profile_skill,
    create_real_run_guardrail_workspace,
    navigation_only_skill,
    run_request_payload,
)


def test_navigation_only_artifact_blocks_before_execution(tmp_path) -> None:
    create_real_run_guardrail_workspace(tmp_path)

    result = persist_stage(
        tmp_path,
        "implement",
        alias="profile-view-unauth",
        payload={"runRequest": run_request_payload(), "skills": [navigation_only_skill()]},
    )

    assert result["status"] == "blocked"
    assert any("specific UI evidence" in blocker["message"] for blocker in result["blockers"])


def test_specific_ui_and_network_evidence_persists(tmp_path) -> None:
    create_real_run_guardrail_workspace(tmp_path)

    result = persist_stage(
        tmp_path,
        "implement",
        alias="profile-view-unauth",
        payload={"runRequest": run_request_payload(), "skills": [coherent_profile_skill()]},
    )

    assert result["status"] == "persisted"
