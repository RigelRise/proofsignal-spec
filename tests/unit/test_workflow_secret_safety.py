from __future__ import annotations

import pytest

from proofsignal_spec.workspace.repository import init_workspace
from proofsignal_spec.workspace.validation import validate_use_case
from proofsignal_spec.workspace.validation import validate_no_secret_values
from proofsignal_spec.workflows.stage_persistence import persist_stage
from proofsignal_spec.workflows.repository import save_workflow_state
from proofsignal_spec.workspace.models import RunProfile
from proofsignal_spec.workflows.models import RepairRecommendation, RuntimeEvidence, UseCaseValidationResult
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


def test_runtime_evidence_and_repair_recommendations_do_not_persist_secret_payloads() -> None:
    evidence = RuntimeEvidence(
        evidenceId="assert-profile-name",
        source="assertion",
        gateId="overview-data-card",
        status="passed",
        specificity="rendered-result",
        artifactRef=".proofsignal/runs/profile-view-unauth/evidence/overview.png",
        redactionStatus="not-sensitive",
    )
    recommendation = RepairRecommendation(
        id="repair-selector-ambiguity",
        category="safe-artifact-repair",
        safeCategory="selector-ambiguity",
        summary="Profile link locator matched multiple elements.",
        action="Narrow selector to a stable, unique target.",
        affectedArtifacts=[".proofsignal/skills/validate-profile-view-unauth-flow.browser.md"],
        sourceFeedback=["strict-mode-violation"],
    )
    result = UseCaseValidationResult(
        alias="profile-view-unauth",
        status="incomplete",
        coreStatus="passed",
        coverageStatus="incomplete",
        repairRecommendations=[recommendation],
        reportPath=".proofsignal/runs/profile-view-unauth/report.json",
        evidenceDir=".proofsignal/runs/profile-view-unauth/evidence",
        exitCode=2,
    )

    assert validate_no_secret_values(evidence.to_dict()) == []
    assert validate_no_secret_values(recommendation.to_dict()) == []
    assert validate_no_secret_values(result.to_dict()) == []


def test_target_environment_handoff_allows_non_secret_url_and_rejects_secret_like_values() -> None:
    safe = {
        "workflow": {
            "stageHandoffDecisions": [
                {
                    "key": "browserTargetEnvironment",
                    "valueSummary": "https://app.example.test",
                    "sourceStage": "clarify",
                    "status": "active",
                }
            ]
        }
    }
    unsafe = {
        "workflow": {
            "stageHandoffDecisions": [
                {
                    "key": "browserTargetEnvironment",
                    "valueSummary": "Bearer abc123abc123abc123abc123",
                    "sourceStage": "clarify",
                    "status": "active",
                }
            ]
        }
    }

    assert validate_no_secret_values(safe) == []
    assert validate_no_secret_values(unsafe)


def test_target_locator_rejects_credential_bearing_urls_and_token_queries() -> None:
    assert validate_no_secret_values({"target": "https://user:pass@example.com/app"})
    assert validate_no_secret_values({"target": "https://example.com/app?token=abc123abc123abc123"})
    assert validate_no_secret_values({"target": "https://example.com/app?api_key=abc123abc123abc123"})
    assert validate_no_secret_values({"target": "https://example.com/app#access_token=abc123abc123abc123"})


def test_target_locator_allows_safe_staging_and_local_urls() -> None:
    assert validate_no_secret_values({"target": "https://app.example.test"}) == []
    assert validate_no_secret_values({"target": "https://app.example.test/profile/jordan-rivera/overview"}) == []
    assert validate_no_secret_values({"target": "http://localhost:5002"}) == []
