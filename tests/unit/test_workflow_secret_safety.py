from __future__ import annotations

import pytest

from proofsignal_spec.workspace.repository import init_workspace
from proofsignal_spec.workspace.validation import validate_use_case
from proofsignal_spec.workflows.stage_persistence import persist_stage
from proofsignal_spec.workflows.repository import save_workflow_state
from proofsignal_spec.workspace.models import RunProfile
from tests.fixtures.workflows.real_run_guardrails import coherent_profile_skill, create_real_run_guardrail_workspace, run_request_payload


def test_workflow_state_rejects_secret_values(tmp_path) -> None:
    init_workspace(tmp_path)
    with pytest.raises(ValueError):
        save_workflow_state(tmp_path, "login", {"schemaVersion": "proofsignal-spec-workflow-state/v1", "password": "real-secret-value"})


def test_stage_persistence_rejects_secret_values(tmp_path) -> None:
    init_workspace(tmp_path)
    result = persist_stage(
        tmp_path,
        "specify",
        alias="login",
        payload={
            "alias": "login",
            "surface": "/login",
            "behavior": "Validate login.",
            "expectedOutcome": "Dashboard.",
            "customSourceReason": "Secret safety fixture.",
            "apiToken": "abc123abc123abc123abc123abc123abc123",
        },
    )
    assert result["status"] == "invalid"


def test_profile_and_gate_metadata_secret_safety(tmp_path) -> None:
    create_real_run_guardrail_workspace(tmp_path)
    result = persist_stage(
        tmp_path,
        "implement",
        alias="profile-view-unauth",
        payload={
            "runRequest": run_request_payload(),
            "skills": [coherent_profile_skill()],
            "profiles": [{"name": "visual-15s", "headed": True, "slowMoMs": 15000}],
        },
    )
    assert result["status"] == "persisted"

    from proofsignal_spec.workspace.repository import load_use_case

    record = load_use_case(tmp_path, "profile-view-unauth")
    assert validate_use_case(tmp_path, record) == []
    record.profiles.append(RunProfile(name="debug-secret", description="bad", headed=True, slowMoMs=-1))
    findings = validate_use_case(tmp_path, record)
    assert any(item["code"] == "invalid-profile-slowmo" for item in findings)
