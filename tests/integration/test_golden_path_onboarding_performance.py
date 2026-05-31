from __future__ import annotations

import time

from proofsignal_spec.integrations.base import build_onboarding_guidance, render_onboarding_guide
from proofsignal_spec.workflows.first_run import build_first_run_recommendation, build_understanding_onboarding_preparation
from tests.fixtures.workflows.golden_path_onboarding import create_onboarding_repository


def test_first_run_recommendation_with_inventory_completes_under_one_second(tmp_path) -> None:
    create_onboarding_repository(tmp_path)

    started = time.perf_counter()
    recommendation = build_first_run_recommendation(tmp_path)
    elapsed = time.perf_counter() - started

    assert elapsed < 1.0
    assert recommendation.status == "ready"


def test_install_guidance_rendering_completes_under_100ms() -> None:
    guide = build_onboarding_guidance(
        integration_key="codex",
        display_name="Codex",
        generated_guide_path=".agents/PROOFSIGNAL_ONBOARDING.md",
    )

    started = time.perf_counter()
    content = render_onboarding_guide(guide)
    elapsed = time.perf_counter() - started

    assert elapsed < 0.1
    assert "ProofSignal Golden Path" in content


def test_clean_repository_onboarding_preparation_is_constant_time_metadata() -> None:
    started = time.perf_counter()
    preparation = build_understanding_onboarding_preparation(stage="specify")
    elapsed = time.perf_counter() - started

    assert elapsed < 0.1
    assert preparation["status"] == "auto-preparable"
