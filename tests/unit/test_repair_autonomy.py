from __future__ import annotations

from proofsignal_spec.workflows.repair_recommendations import classify_repair_findings


def test_safe_mechanical_repairs_are_auto_applicable_when_intent_preserved() -> None:
    recommendations = classify_repair_findings(
        [
            {"code": "wait-timeout", "message": "Step timed out waiting for a rendered slider."},
            {"code": "strict-mode-violation", "message": "Locator matched multiple elements."},
            {"code": "main-skill-ordering", "message": "Helper skill executed before main skill."},
            {"code": "debug-slowmo-default", "message": "Debug run has slowMoMs 0."},
        ]
    )

    assert {item.safeCategory for item in recommendations} == {
        "wait-strategy",
        "selector-ambiguity",
        "main-skill-ordering",
        "run-profile-defaults",
    }
    assert all(item.safeMechanical for item in recommendations)
    assert all(item.autonomy == "auto-applied" for item in recommendations)
    assert not any(item.requiresUserDecision for item in recommendations)


def test_data_credential_and_gate_intent_repairs_require_confirmation_or_block() -> None:
    recommendations = classify_repair_findings(
        [
            {"code": "missing-gateid", "message": "assertion lacks gateId"},
            {"code": "seeded-data-change", "message": "Change data assumptions for empty state."},
            {"code": "credential-reference-change", "message": "Update credential requirement."},
            {"code": "expected-behavior-change", "message": "Expected product behavior is different."},
        ]
    )

    by_id = {item.id: item for item in recommendations}
    assert any(item.safeCategory == "gateid-mapping" and item.autonomy == "confirmation-required" for item in recommendations)
    assert all(item.autonomy in {"confirmation-required", "blocked"} for item in by_id.values())
    assert all(item.requiresUserDecision for item in by_id.values())
