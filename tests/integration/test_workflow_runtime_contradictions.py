from __future__ import annotations

from proofsignal_spec.workflows.repair_recommendations import classify_repair_findings
from proofsignal_spec.workflows.runtime_readiness import evaluate_runtime_readiness
from proofsignal_spec.workspace.models import ArtifactReference, RuntimeInputRequirement, UseCaseRecord
from proofsignal_spec.workspace.repository import init_workspace, save_document, save_use_case


def test_dynamic_discovery_to_fixed_profile_repair_requires_clarification() -> None:
    recommendations = classify_repair_findings(
        [
            {
                "code": "hardcoded-profile-replacement",
                "message": "Replace dynamic discovery via search with fixed profile casey-morgan.",
                "path": "steps[0]",
            }
        ]
    )

    assert recommendations[0].category == "clarification-required"
    assert recommendations[0].requiresUserDecision is True
    assert "clarified" in (recommendations[0].blockedReason or "")


def test_empty_target_after_resolution_is_stage_handoff_defect(tmp_path) -> None:
    init_workspace(tmp_path)
    run_request = ".proofsignal/run-requests/profile.yaml"
    skill = ".proofsignal/skills/profile.browser.md"
    (tmp_path / ".proofsignal/run-requests").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".proofsignal/skills").mkdir(parents=True, exist_ok=True)
    save_document(
        tmp_path / run_request,
        {
            "schemaVersion": "qa-run-request/v1",
            "target": "browser",
            "parameters": {"baseUrl": ""},
            "skills": [{"id": "skill.profile", "version": "1.0.0"}],
        },
    )
    (tmp_path / skill).write_text("# Profile\n", encoding="utf-8")
    save_use_case(
        tmp_path,
        UseCaseRecord(
            alias="profile",
            title="Profile",
            description="Validate profile.",
            runRequest=ArtifactReference(path=run_request, kind="run-request"),
            mainSkill=ArtifactReference(path=skill, kind="skill"),
            skills=[ArtifactReference(path=skill, kind="skill")],
            runtimeInputs=[RuntimeInputRequirement(name="baseUrl", required=True)],
            workflow={
                "stageHandoffDecisions": [
                    {
                        "key": "browserTargetEnvironment",
                        "valueSummary": "https://app.example.test",
                        "sourceStage": "clarify",
                        "status": "active",
                    }
                ]
            },
        ),
    )

    readiness = evaluate_runtime_readiness(tmp_path, "profile", authoring_result={"status": "passed"})

    assert readiness.status == "blocked"
    assert readiness.targetResolutionStatus == "resolved"
    assert "runtime.stage-handoff-defect.baseUrl-empty-after-resolution" in readiness.findingIds
