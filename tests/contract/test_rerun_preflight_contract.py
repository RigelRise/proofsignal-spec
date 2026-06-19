from __future__ import annotations

from proofsignal_spec.workflows.write_safety import evaluate_rerun_decision

from tests.fixtures.workflows.side_effect_contract_alignment import blocked_write_last_run, create_write_policy_workspace


def test_effective_rerun_decision_contract_covers_allowed_confirmation_and_blocked(tmp_path) -> None:
    fresh = create_write_policy_workspace(tmp_path / "fresh")
    assert evaluate_rerun_decision(fresh)["decision"] == "allowed"

    blocked = create_write_policy_workspace(tmp_path / "blocked", last_run=blocked_write_last_run())
    assert evaluate_rerun_decision(blocked)["decision"] == "blocked"

    confirmation = create_write_policy_workspace(tmp_path / "confirmation", last_run=_last_run("requires-confirmation"))
    assert evaluate_rerun_decision(confirmation)["decision"] == "requires-confirmation"

    allowed_new = create_write_policy_workspace(tmp_path / "allowed-new", last_run=_last_run("safe-with-new-inputs"))
    assert evaluate_rerun_decision(allowed_new)["decision"] == "allowed-with-new-inputs"


def _last_run(risk: str) -> dict:
    return {
        "runId": f"run-{risk}",
        "status": "passed",
        "postCommitInterpretation": {
            "postCommit": True,
            "sideEffectMayExist": True,
            "failurePhase": "post-commit",
            "sideEffectStatus": "committed-confirmed",
            "rerunRisk": risk,
        },
    }
