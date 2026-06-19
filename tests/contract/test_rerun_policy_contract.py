from __future__ import annotations

from proofsignal_spec.workspace.models import RerunPolicy
from proofsignal_spec.workflows.repair_recommendations import combine_rerun_decision


def test_canonical_rerun_policy_accepts_allowed_with_new_inputs() -> None:
    policy = RerunPolicy.from_dict(
        {
            "afterNoCommit": "allowed",
            "afterCommit": "allowed-with-new-inputs",
            "afterUnknown": "requires-confirmation",
            "refreshRuntimeInputs": ["projectTitle"],
        }
    )

    assert policy.afterCommit == "allowed-with-new-inputs"
    assert policy.validate(refreshable_inputs=["projectTitle"]) == []


def test_legacy_safe_with_new_inputs_policy_migrates_to_after_commit() -> None:
    policy = RerunPolicy.from_dict({"rerunRisk": "safe-with-new-inputs", "refreshRuntimeInputs": ["projectTitle"]})

    assert policy.afterCommit == "allowed-with-new-inputs"
    assert policy.refreshRuntimeInputs == ["projectTitle"]
    assert policy.validate(refreshable_inputs=["projectTitle"]) == []


def test_legacy_safe_with_new_inputs_without_refresh_inputs_is_ambiguous() -> None:
    policy = RerunPolicy.from_dict({"rerunRisk": "safe-with-new-inputs"})

    findings = policy.validate(refreshable_inputs=["projectTitle"])

    assert any(item["code"] == "rerun-policy-legacy-ambiguous" for item in findings)


def test_combines_core_and_spec_risk_by_most_restrictive_decision() -> None:
    assert combine_rerun_decision("safe", "allowed-with-new-inputs") == "allowed-with-new-inputs"
    assert combine_rerun_decision("safe-with-new-inputs", "allowed") == "allowed-with-new-inputs"
    assert combine_rerun_decision("requires-confirmation", "allowed-with-new-inputs") == "requires-confirmation"
    assert combine_rerun_decision("blocked", "allowed-with-new-inputs") == "blocked"
