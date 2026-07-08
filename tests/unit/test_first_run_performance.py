from __future__ import annotations

import time

from verifysignal_spec.workflows.first_run import score_first_run_candidates
from verifysignal_spec.workflows.models import CandidateValidationUseCase
from verifysignal_spec.workflows.stage_cards import build_stage_card


def test_first_run_candidate_ranking_completes_under_one_second() -> None:
    candidates = [
        CandidateValidationUseCase(
            alias=f"candidate-{index}",
            surface=f"/page-{index}",
            behavior="Simple rendered public page.",
            sourceInventoryItems=[f"route-{index}"],
            rationale="Generated performance candidate.",
            confidence="high" if index == 3 else "medium",
            priority="critical" if index == 3 else "medium",
            requiresEnvironment=True,
            knownRuntimeRequirements=["baseUrl"],
        )
        for index in range(1000)
    ]

    started = time.perf_counter()
    ranked = score_first_run_candidates(candidates, target_status="resolved", inventory_status="complete")
    elapsed = time.perf_counter() - started

    assert elapsed < 1.0
    assert ranked[0].rank == 1
    assert ranked[0].score >= ranked[-1].score


def test_stage_card_generation_completes_under_100ms() -> None:
    started = time.perf_counter()
    cards = [
        build_stage_card(
            stage_id=f"stage-{index}",
            title="Golden Path Stage",
            status_marker="[RUNNING]",
            summary="Stage is running.",
            why_it_matters="Users need clear progress.",
            primary_evidence="Structured workflow state.",
            next_action="Continue.",
        )
        for index in range(500)
    ]
    elapsed = time.perf_counter() - started

    assert elapsed < 0.1
    assert len(cards) == 500
