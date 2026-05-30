from __future__ import annotations

from proofsignal_spec.workflows.first_run import classify_first_run_blocker


def test_first_run_blocker_contract_has_recovery_action_and_stage_card() -> None:
    for code in ["missing-target", "unreachable-target", "unresolved-credentials", "stale-inventory", "incompatible-core"]:
        blocker = classify_first_run_blocker(code, alias="home-page-unauth")

        assert blocker["status"] == "blocked"
        assert blocker["category"]
        assert blocker["nextAction"]
        assert blocker["stageCards"][0]["statusMarker"] == "[BLOCKED]"
        assert blocker["stageCards"][0]["primaryEvidence"]
