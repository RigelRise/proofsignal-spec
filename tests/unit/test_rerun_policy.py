from __future__ import annotations

from verifysignal_spec.workspace.models import RerunPolicy
from verifysignal_spec.workflows.repair_recommendations import combine_rerun_decision


def test_rerun_policy_requires_refreshable_inputs_for_allowed_with_new_inputs() -> None:
    policy = RerunPolicy.from_dict({"afterNoCommit": "allowed", "afterCommit": "allowed-with-new-inputs"})

    findings = policy.validate(refreshable_inputs=[])

    assert any(item["code"] == "rerun-refresh-input-missing" for item in findings)


def test_most_restrictive_rerun_decision_wins() -> None:
    assert combine_rerun_decision(core_risk="blocked", spec_decision="allowed") == "blocked"
    assert combine_rerun_decision(core_risk="safe", spec_decision="requires-confirmation") == "requires-confirmation"
    assert combine_rerun_decision(core_risk="safe-with-new-inputs", spec_decision="allowed") == "allowed-with-new-inputs"

