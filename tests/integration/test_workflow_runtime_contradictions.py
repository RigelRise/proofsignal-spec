from __future__ import annotations

from proofsignal_spec.workflows.repair_recommendations import classify_repair_findings


def test_dynamic_discovery_to_fixed_profile_repair_requires_clarification() -> None:
    recommendations = classify_repair_findings(
        [
            {
                "code": "hardcoded-profile-replacement",
                "message": "Replace dynamic discovery via search with fixed profile casey-morgan.",
                "path": "steps[0]",
            }
        ]
    )

    assert recommendations[0].category == "clarification-required"
    assert recommendations[0].requiresUserDecision is True
    assert "clarified" in (recommendations[0].blockedReason or "")
