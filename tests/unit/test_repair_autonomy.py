from __future__ import annotations

from verifysignal_spec.workflows.repair_recommendations import MUTABLE_SAFE_CATEGORIES, classify_repair_findings


def test_safe_mechanical_repair_autonomy_matches_the_available_mutator() -> None:
    # RATCHET: `autonomy` must describe the MECHANISM that exists, not an aspiration. Only
    # main-skill-ordering has a real on-disk mutator (_apply_safe_artifact_repair); the rest need live
    # page/DOM context or render into no artifact, so they are `propose-only` — described, not applied.
    # (Bug: all four were labeled `auto-applied` while three could never apply anything, which drove an
    # "after" and a stage card reading as if the fix had landed.)
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
    assert {item.safeCategory: item.autonomy for item in recommendations} == {
        "main-skill-ordering": "auto-applied",
        "wait-strategy": "propose-only",
        "selector-ambiguity": "propose-only",
        "run-profile-defaults": "propose-only",
    }
    # The invariant itself, so a NEW category can never be labeled auto-applied without a mutator (and
    # adding a mutator flips its label automatically — the two cannot drift apart).
    for item in recommendations:
        assert (item.autonomy == "auto-applied") == (item.safeCategory in MUTABLE_SAFE_CATEGORIES)
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
