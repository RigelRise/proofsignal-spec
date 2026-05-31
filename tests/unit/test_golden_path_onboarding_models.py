from __future__ import annotations

import pytest

from proofsignal_spec.workflows.models import (
    FirstRunIdealCriteria,
    FirstRunSuitabilityScore,
    GuidedFirstRunState,
    OnboardingGuidance,
    UnderstandingOnboardingResult,
)


def test_ideal_criteria_reports_met_and_missing_fields() -> None:
    criteria = FirstRunIdealCriteria(
        publicOrUnauthenticated=True,
        readOnly=True,
        singleVisibleSurface=True,
        stableRenderedEvidence=False,
        noCredentials=True,
        lowExternalDependency=False,
        safeToAutoGuide=False,
    )

    assert criteria.met() == ["publicOrUnauthenticated", "readOnly", "singleVisibleSurface", "noCredentials"]
    assert criteria.missing() == ["stableRenderedEvidence", "lowExternalDependency", "safeToAutoGuide"]

    round_trip = FirstRunIdealCriteria.from_dict(criteria.to_dict())
    assert round_trip.readOnly is True
    assert round_trip.lowExternalDependency is False


def test_suitability_score_round_trips_with_explicit_acceptance_gap() -> None:
    score = FirstRunSuitabilityScore(
        candidateAlias="authenticated-lowest-risk",
        rank=1,
        score=61,
        idealCriteriaMet=["readOnly", "singleVisibleSurface"],
        idealCriteriaMissing=["publicOrUnauthenticated", "noCredentials"],
        requiresExplicitAcceptance=True,
        branchRelevant=False,
        suitabilityRationale="Lowest-risk available candidate, but credentials are required.",
        blockers=[],
        sourceInventoryItems=["route-dashboard"],
    )

    data = score.to_dict()
    assert data["requiresExplicitAcceptance"] is True
    assert data["idealCriteriaMissing"] == ["publicOrUnauthenticated", "noCredentials"]

    round_trip = FirstRunSuitabilityScore.from_dict(data)
    assert round_trip.candidateAlias == "authenticated-lowest-risk"
    assert round_trip.sourceInventoryItems == ["route-dashboard"]


def test_guided_first_run_state_validates_stage_and_round_trips() -> None:
    state = GuidedFirstRunState(
        selectedCandidate="home-page-unauth",
        stage="repairing",
        firstRunStatus="repairing",
        strictPass=False,
        resumeCommand="proofsignal-spec repair home-page-unauth --json",
        stageCards=[
            {
                "stageId": "repairing",
                "title": "Safe Repair",
                "statusMarker": "[REPAIR]",
                "summary": "A safe wait repair is being applied.",
                "whyItMatters": "Repair can still produce a successful first run.",
                "primaryEvidence": "Core reported a wait timing failure.",
                "nextAction": "Revalidate and rerun.",
                "repairDetails": "Increase the wait for rendered slider evidence.",
            }
        ],
        ownedArtifacts=[".proofsignal/run-requests/home-page-unauth.yaml"],
    )

    data = state.to_dict()
    assert data["schemaVersion"] == "proofsignal-spec-guided-first-run/v1"
    assert data["stageCards"][0]["statusMarker"] == "[REPAIR]"
    assert GuidedFirstRunState.from_dict(data).stage == "repairing"

    with pytest.raises(ValueError):
        GuidedFirstRunState(selectedCandidate="home-page-unauth", stage="unknown").to_dict()


def test_onboarding_guidance_round_trips_without_secret_values() -> None:
    guide = OnboardingGuidance(
        integrationKey="codex",
        terminalTitle="ProofSignal Golden Path",
        terminalSummary="Run /proofsignal-specify to start the recommended first validation.",
        generatedGuidePath=".agents/PROOFSIGNAL_ONBOARDING.md",
        stageMarkers=["[RECOMMENDED]", "[ACCEPTED]", "[PASS]", "[REPAIR]", "[BLOCKED]"],
        usesColor=True,
        plainTextFallback="ProofSignal Golden Path\nNext: /proofsignal-specify",
        nextCommand="/proofsignal-specify",
        safetyBoundaries=["Sensitive files and credential values are not inspected or persisted by default."],
        successSemantics=["Direct strict pass succeeds.", "Repaired strict pass also succeeds."],
    )

    data = guide.to_dict()
    assert data["usesColor"] is True
    assert "credential values" in data["safetyBoundaries"][0]
    assert OnboardingGuidance.from_dict(data).generatedGuidePath == ".agents/PROOFSIGNAL_ONBOARDING.md"


def test_understanding_onboarding_result_round_trips_partial_inventory() -> None:
    result = UnderstandingOnboardingResult(
        status="partial",
        scope="all",
        generatedGitHash="abc1234",
        sourceFilesVisited=12,
        candidateCount=2,
        trivialCandidateCount=1,
        sourceTraceabilityStatus="normalized",
        partialInventoryReasons=["admin routes were not inspected"],
        nextAction="Continue understanding with scope continue.",
    )

    data = result.to_dict()
    assert data["partialInventoryReasons"] == ["admin routes were not inspected"]
    assert UnderstandingOnboardingResult.from_dict(data).sourceTraceabilityStatus == "normalized"
