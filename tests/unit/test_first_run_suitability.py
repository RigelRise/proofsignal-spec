from __future__ import annotations

from proofsignal_spec.workflows.first_run import evaluate_first_run_ideal_criteria, score_first_run_candidates
from proofsignal_spec.workflows.models import CandidateValidationUseCase, FirstRunCandidate


def test_public_read_only_rendered_candidate_beats_credential_write_candidate() -> None:
    public = CandidateValidationUseCase(
        alias="home-page-unauth",
        surface="/",
        behavior="Public unauthenticated page renders stable hero content.",
        sourceInventoryItems=["route-home"],
        rationale="Simple public page.",
        priority="medium",
        confidence="high",
        requiresEnvironment=True,
        knownRuntimeRequirements=["baseUrl"],
    )
    branch = CandidateValidationUseCase(
        alias="project-multi-actor-add-people",
        surface="/project/[path]",
        behavior="Active branch flow writes contributors after login.",
        sourceInventoryItems=["route-project"],
        rationale="Active branch work.",
        priority="critical",
        confidence="high",
        requiresEnvironment=True,
        knownRuntimeRequirements=["baseUrl", "credential:ba-user", "write operation", "active branch"],
    )

    scores = score_first_run_candidates([branch, public], target_status="resolved", inventory_status="complete")

    assert scores[0].candidateAlias == "home-page-unauth"
    assert scores[0].idealCriteriaMissing == []
    assert scores[1].branchRelevant is True
    assert "readOnly" in scores[1].idealCriteriaMissing
    assert "noCredentials" in scores[1].idealCriteriaMissing


def test_no_ideal_candidate_is_marked_for_explicit_acceptance() -> None:
    auth_read_only = FirstRunCandidate(
        alias="settings-auth",
        surface="/settings",
        behavior="Authenticated settings page renders visible account data.",
        sourceInventoryItems=["route-settings"],
        priority="medium",
        confidence="high",
        requiresEnvironment=True,
        knownRuntimeRequirements=["baseUrl", "credential:user"],
    )

    score = score_first_run_candidates([auth_read_only], target_status="resolved", inventory_status="complete")[0]

    assert score.requiresExplicitAcceptance is True
    assert "publicOrUnauthenticated" in score.idealCriteriaMissing
    assert "noCredentials" in score.idealCriteriaMissing


def test_ideal_criteria_flags_external_and_data_dependencies() -> None:
    candidate = FirstRunCandidate(
        alias="activity-data",
        surface="/",
        behavior="Activity slider renders only when seeded activity data exists.",
        sourceInventoryItems=["route-home"],
        knownRuntimeRequirements=["baseUrl", "seeded activity data"],
    )

    criteria = evaluate_first_run_ideal_criteria(candidate)

    assert criteria.publicOrUnauthenticated is True
    assert criteria.lowExternalDependency is False
    assert criteria.safeToAutoGuide is False
