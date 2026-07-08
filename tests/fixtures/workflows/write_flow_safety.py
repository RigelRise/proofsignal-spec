from __future__ import annotations

from typing import Any


def read_only_use_case_payload(alias: str = "about-page-unauth") -> dict[str, Any]:
    return {
        "alias": alias,
        "surface": "/about",
        "behavior": "Validate the public about page renders.",
        "expectedOutcome": "The about page loads without authentication.",
        "customSourceReason": "Write-flow safety fixture.",
        "sideEffects": {"class": "none"},
    }


def write_use_case_payload(alias: str = "create-resource") -> dict[str, Any]:
    return {
        "alias": alias,
        "surface": "/resources/new",
        "behavior": "Create a test resource.",
        "expectedOutcome": "A test resource is created and the final resource page renders.",
        "customSourceReason": "Write-flow safety fixture.",
        "sideEffects": {
            "class": "write",
            "commitStepId": "submit-resource",
            "allowed": [{"id": "create-resource", "kind": "network", "methods": ["POST"], "urlContains": "/resources"}],
            "confirmationSignals": [{"id": "created-url", "type": "finalUrl", "pattern": "/resources/"}],
        },
        "runtimeInputs": [
            {
                "name": "resourceName",
                "source": "generated",
                "template": "VerifySignal {{run.shortId}}",
                "refreshOnRerunAfterCommit": True,
            }
        ],
        "runtimeOutputs": [{"name": "createdResourceUrl", "source": "finalUrl"}],
        "rerunPolicy": {"afterNoCommit": "allowed", "afterCommit": "allowed-with-new-inputs", "refreshInputs": ["resourceName"]},
    }


def post_commit_core_result() -> dict[str, Any]:
    return {
        "sideEffects": {"commitStep": {"id": "submit-resource", "reached": True, "status": "passed"}},
        "runtimeOutputs": [{"name": "createdResourceUrl", "source": "finalUrl", "status": "captured", "value": "/resources/example"}],
        "resultClassification": {
            "executionStatus": "passed",
            "verificationStatus": "failed",
            "sideEffectStatus": "likely-committed",
            "failurePhase": "post-commit",
            "rerunRisk": "requires-confirmation",
            "recommendedAction": "review-created-resource-before-rerun",
            "reasons": ["verification-selector-timeout"],
        },
    }
