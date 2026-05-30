from __future__ import annotations

from proofsignal_spec.workflows.models import GoldenPathRunState


def test_golden_path_run_result_strict_pass_contract() -> None:
    state = GoldenPathRunState.from_run_result(
        use_case_alias="home-page-unauth",
        target="https://app.example.test",
        core_browser_status="passed",
        spec_coverage_status="complete",
        missing_required_gates=[],
    ).to_dict()

    assert state["firstRunStatus"] == "passed"
    assert state["strictPass"] is True
    assert state["coreBrowserStatus"] == "passed"
    assert state["specCoverageStatus"] == "complete"
    assert state["missingRequiredGates"] == []


def test_golden_path_run_result_incomplete_is_not_success() -> None:
    state = GoldenPathRunState.from_run_result(
        use_case_alias="home-page-unauth",
        target="https://app.example.test",
        core_browser_status="passed",
        spec_coverage_status="incomplete",
        missing_required_gates=["home-activity-slider"],
    ).to_dict()

    assert state["firstRunStatus"] == "incomplete"
    assert state["strictPass"] is False


def test_golden_path_run_result_repaired_pass_requires_final_strict_pass() -> None:
    state = GoldenPathRunState.from_run_result(
        use_case_alias="home-page-unauth",
        target="https://app.example.test",
        core_browser_status="passed",
        spec_coverage_status="complete",
        missing_required_gates=[],
        repaired=True,
        repair_feedback=[{"repairId": "repair-wait", "autonomy": "auto-applied"}],
    ).to_dict()

    assert state["firstRunStatus"] == "repaired-passed"
    assert state["strictPass"] is True
    assert state["repairFeedback"][0]["autonomy"] == "auto-applied"
