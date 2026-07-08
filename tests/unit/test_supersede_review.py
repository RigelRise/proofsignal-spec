from __future__ import annotations

from verifysignal_spec.workspace.models import SupersedeReview
from verifysignal_spec.workflows.write_safety import evaluate_rerun_decision

from tests.fixtures.workflows.side_effect_contract_alignment import blocked_write_last_run, create_write_policy_workspace, supersede_review_payload


def test_supersede_review_requires_audit_fields() -> None:
    review = SupersedeReview.from_dict({"reviewId": "review-1"})

    codes = {item["code"] for item in review.validate()}

    assert "supersede-review-field-missing" in codes
    assert "supersede-review-previous-missing" in codes
    assert "supersede-review-resulting-missing" in codes


def test_supersede_review_changes_effective_rerun_decision_without_mutating_last_run(tmp_path) -> None:
    record = create_write_policy_workspace(tmp_path, last_run=blocked_write_last_run())
    original_last_run = dict(record.lastRun)
    review = SupersedeReview.from_dict(supersede_review_payload(source_run_id=record.lastRun["runId"]))

    decision = evaluate_rerun_decision(record, supersede_reviews=[review])

    assert decision["decision"] == "allowed-with-new-inputs"
    assert decision["coreRisk"] == "safe-with-new-inputs"
    assert record.lastRun == original_last_run
