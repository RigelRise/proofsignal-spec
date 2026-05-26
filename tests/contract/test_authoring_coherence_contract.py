from __future__ import annotations

from proofsignal_spec.workflows.authoring_coherence import evaluate_implementation_coherence, normalize_artifact_aliases
from proofsignal_spec.workflows.stage_persistence import persist_stage
from proofsignal_spec.workspace.repository import load_document, load_use_case

from tests.fixtures.workflows.real_run_guardrails import (
    coherent_profile_skill,
    create_real_run_guardrail_workspace,
    navigation_only_skill,
    run_request_payload,
)


def test_planned_main_skill_selected_when_helper_is_first(tmp_path) -> None:
    create_real_run_guardrail_workspace(tmp_path)
    payload = {
        "runRequest": run_request_payload(skills_first=["skill.navigate-to-profile", "skill.validate-profile-view-unauth-flow"]),
        "skills": [
            coherent_profile_skill(".proofsignal/skills/navigate-to-profile.browser.md"),
            coherent_profile_skill(".proofsignal/skills/validate-profile-view-unauth-flow.browser.md"),
        ],
        "runtimeInputs": [{"name": "baseUrl", "default": "https://app.example.test"}],
    }

    result = persist_stage(tmp_path, "implement", alias="profile-view-unauth", payload=payload)

    assert result["status"] == "persisted"
    record = load_use_case(tmp_path, "profile-view-unauth")
    assert record.mainSkill
    assert record.mainSkill.path == ".proofsignal/skills/validate-profile-view-unauth-flow.browser.md"
    run_request = load_document(tmp_path / ".proofsignal/run-requests/profile-view-unauth.yaml")
    assert run_request["skills"][0]["id"] == "skill.validate-profile-view-unauth-flow"


def test_missing_planned_main_skill_blocks_implementation(tmp_path) -> None:
    create_real_run_guardrail_workspace(tmp_path)
    payload = {
        "runRequest": run_request_payload(),
        "skills": [coherent_profile_skill(".proofsignal/skills/navigate-to-profile.browser.md")],
        "runtimeInputs": [{"name": "baseUrl", "default": "https://app.example.test"}],
    }

    result = persist_stage(tmp_path, "implement", alias="profile-view-unauth", payload=payload)

    assert result["status"] == "blocked"
    assert "Planned main validation skill is missing" in result["blockers"][0]["message"]


def test_malformed_payload_aliases_are_normalized_and_reported(tmp_path) -> None:
    create_real_run_guardrail_workspace(tmp_path)
    payload = {
        "runRequest": {"artifactPath": ".proofsignal/run-requests/profile-view-unauth.yaml", "artifactKind": "run-request"},
        "skills": [
            {
                **coherent_profile_skill(".proofsignal/skills/validate-profile-view-unauth-flow.browser.md"),
                "artifactPath": ".proofsignal/skills/validate-profile-view-unauth-flow.browser.md",
                "artifactKind": "skill",
            }
        ],
    }

    normalized = normalize_artifact_aliases(payload)
    result = evaluate_implementation_coherence(tmp_path, "profile-view-unauth", normalized)

    assert result.status == "passed"
    assert result.normalizedAliases == []


def test_navigation_only_page_view_is_incoherent(tmp_path) -> None:
    create_real_run_guardrail_workspace(tmp_path)
    result = evaluate_implementation_coherence(
        tmp_path,
        "profile-view-unauth",
        {"runRequest": run_request_payload(), "skills": [navigation_only_skill()]},
    )

    assert result.status == "blocked"
    assert any("overview-data-card" in blocker for blocker in result.blockers)
