from __future__ import annotations

from verifysignal_spec.workflows.models import (
    FirstRunIdealCriteria,
    FirstRunSuitabilityScore,
    GuidedFirstRunState,
    OnboardingGuidance,
    UnderstandingOnboardingResult,
)


def test_first_run_suitability_score_contract_fields() -> None:
    score = FirstRunSuitabilityScore(
        candidateAlias="home-page-unauth",
        rank=1,
        score=98,
        idealCriteriaMet=["publicOrUnauthenticated", "readOnly"],
        idealCriteriaMissing=[],
        requiresExplicitAcceptance=False,
        branchRelevant=False,
        suitabilityRationale="Public read-only rendered page.",
        sourceInventoryItems=["route-home"],
    ).to_dict()

    assert score["candidateAlias"] == "home-page-unauth"
    assert score["sourceInventoryItems"] == ["route-home"]
    assert score["requiresExplicitAcceptance"] is False


def test_shared_onboarding_model_round_trips() -> None:
    criteria = FirstRunIdealCriteria(publicOrUnauthenticated=True, readOnly=True).to_dict()
    assert criteria["publicOrUnauthenticated"] is True
    assert "stableRenderedEvidence" in criteria

    state = GuidedFirstRunState(
        selectedCandidate="home-page-unauth",
        stage="accepted",
        firstRunStatus="not-started",
        resumeCommand="verifysignal validate home-page-unauth --runtime-readiness --json",
    ).to_dict()
    assert state["schemaVersion"] == "verifysignal-spec-guided-first-run/v1"
    assert state["stage"] == "accepted"
    assert state["resumeCommand"].startswith("verifysignal validate")

    guide = OnboardingGuidance(
        integrationKey="codex",
        terminalTitle="VerifySignal Golden Path",
        terminalSummary="Run /verifysignal-specify next.",
        generatedGuidePath=".agents/VERIFYSIGNAL_ONBOARDING.md",
        stageMarkers=["[RECOMMENDED]", "[PASS]"],
        safetyBoundaries=["Sensitive files require approval."],
        successSemantics=["repaired-passed counts as success"],
        plainTextFallback="VerifySignal Golden Path: run /verifysignal-specify next.",
        nextCommand="/verifysignal-specify",
    ).to_dict()
    assert guide["nextCommand"] == "/verifysignal-specify"
    assert "repaired-passed" in " ".join(guide["successSemantics"])

    result = UnderstandingOnboardingResult(
        status="complete",
        scope="all",
        generatedGitHash="abc1234",
        sourceFilesVisited=42,
        candidateCount=3,
        trivialCandidateCount=1,
        sourceTraceabilityStatus="complete",
    ).to_dict()
    assert result["candidateCount"] == 3
    assert result["sourceTraceabilityStatus"] == "complete"
