from __future__ import annotations

from tests.fixtures.workflows.side_effect_contract_alignment import conflicting_policy, legacy_rules_policy

from proofsignal_spec.workflows.write_safety import normalize_side_effect_policy


def test_unambiguous_legacy_rules_migrate_to_allowed_and_forbidden_without_mode_change() -> None:
    canonical, findings = normalize_side_effect_policy(legacy_rules_policy(mode="observe"))

    assert canonical["mode"] == "observe"
    assert "rules" not in canonical
    assert canonical["allowed"] == [{"id": "allow-backend-graphql", "kind": "network", "methods": ["POST"], "urlContains": "be.example.test/graphql"}]
    assert canonical["forbidden"] == [{"id": "forbid-admin", "kind": "network", "methods": [], "urlContains": "/admin"}]
    assert any(item["code"] == "legacy-side-effect-rules" and item["migrationAvailable"] for item in findings)
    assert not any(item["severity"] == "blocking" for item in findings)


def test_canonical_rules_are_normalized_to_core_rule_shape() -> None:
    canonical, findings = normalize_side_effect_policy(
        {
            "class": "write",
            "mode": "enforce",
            "commitStepId": "confirm-publish-dialog",
            "allowed": [{"id": "allow-backend-graphql", "urlContains": "be.example.test/graphql", "method": "post"}],
            "forbidden": [{"id": "forbid-admin", "kind": "network", "urlContains": "/admin"}],
            "confirmationSignals": [],
        }
    )

    assert canonical["allowed"] == [{"id": "allow-backend-graphql", "kind": "network", "methods": ["POST"], "urlContains": "be.example.test/graphql"}]
    assert canonical["forbidden"] == [{"id": "forbid-admin", "kind": "network", "methods": [], "urlContains": "/admin"}]
    assert "method" not in canonical["allowed"][0]
    assert not any(item["severity"] == "blocking" for item in findings)


def test_rule_without_id_blocks_instead_of_generating_identity() -> None:
    canonical, findings = normalize_side_effect_policy(
        {
            "class": "write",
            "mode": "enforce",
            "commitStepId": "confirm-publish-dialog",
            "allowed": [{"urlContains": "be.example.test/graphql", "method": "POST"}],
            "confirmationSignals": [],
        }
    )

    assert canonical["allowed"] == [{"urlContains": "be.example.test/graphql", "method": "POST"}]
    blocking = [item for item in findings if item["severity"] == "blocking"]
    assert blocking
    assert blocking[0]["code"] == "side-effect-rule-missing-id"
    assert {choice["id"] for choice in blocking[0]["guidedChoices"]} >= {"keep-canonical", "migrate-legacy", "ask-owner"}


def test_conflicting_legacy_and_canonical_policy_blocks_with_guided_choices() -> None:
    canonical, findings = normalize_side_effect_policy(conflicting_policy())

    assert canonical["allowed"] == [{"id": "canonical-different", "kind": "network", "methods": [], "urlContains": "api.example.test"}]
    blocking = [item for item in findings if item["severity"] == "blocking"]
    assert blocking
    assert blocking[0]["code"] == "conflicting-side-effect-policy"
    assert {choice["id"] for choice in blocking[0]["guidedChoices"]} >= {"keep-canonical", "migrate-legacy", "ask-owner"}
