from __future__ import annotations

from proofsignal_spec.workspace.models import PostCommitInterpretation


def test_post_commit_interpretation_warns_when_commit_reached_and_verification_failed() -> None:
    interpretation = PostCommitInterpretation.from_core_result(
        {
            "sideEffects": {"commitStep": {"id": "submit", "reached": True, "status": "passed"}},
            "resultClassification": {
                "executionStatus": "passed",
                "verificationStatus": "failed",
                "sideEffectStatus": "likely-committed",
                "failurePhase": "post-commit",
                "rerunRisk": "requires-confirmation",
                "recommendedAction": "review-created-resource-before-rerun",
                "reasons": ["verification-timeout"],
            },
        }
    )

    assert interpretation.postCommit is True
    assert interpretation.sideEffectMayExist is True
    assert "may already exist" in interpretation.specMessage
    assert interpretation.to_dict()["failurePhase"] == "post-commit"

