from __future__ import annotations

from proofsignal_spec.workflows.repair_classification import classify_runtime_feedback


def test_wait_flow_timeout_is_classified_with_high_confidence() -> None:
    finding = classify_runtime_feedback(
        {
            "code": "wait-timeout",
            "message": "Step scroll-to-activity timed out waiting for .swiper-slide while activity skeletons were visible.",
            "gateId": "home-activity-slider",
        }
    )

    assert finding.category == "wait-flow-issue"
    assert finding.recommendedAction == "implement-repair"
    assert finding.confidence == "high"
    assert finding.affectedGates == ["home-activity-slider"]


def test_selector_failure_is_classified_separately_from_wait_flow() -> None:
    finding = classify_runtime_feedback({"code": "strict-mode-violation", "message": "Locator matched multiple elements."})

    assert finding.category == "selector-issue"
    assert finding.recommendedAction == "implement-repair"


def test_aborted_run_missing_coverage_is_diagnostic_mapping_issue() -> None:
    finding = classify_runtime_feedback({"code": "missing-gate-coverage", "message": "No mapped evidence was found because Core/browser execution failed."})

    assert finding.category == "coverage-mapping-issue"
    assert finding.severity == "warning"
    assert finding.recommendedAction == "implement-repair"
