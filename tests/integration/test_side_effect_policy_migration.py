from __future__ import annotations

from verifysignal_spec.workspace.repository import load_use_case
from verifysignal_spec.workflows.stage_persistence import persist_stage

from tests.fixtures.workflows.side_effect_contract_alignment import conflicting_policy, create_write_policy_workspace, legacy_rules_policy


def _payload(side_effects: dict) -> dict:
    return {
        "runRequest": {"path": ".verifysignal/run-requests/add-collaboration-project.yaml"},
        "runtimeInputs": [
            {"name": "baseUrl", "source": "default", "value": "https://example.test"},
            {"name": "projectTitle", "source": "generated", "value": "VerifySignal collab seed", "refreshOnRerunAfterCommit": True},
        ],
        "skills": [
            {
                "path": ".verifysignal/skills/add-collaboration-project.browser.md",
                "kind": "skill",
                "intent": {"browser": {"targets": {"page": {"css": "body"}}, "steps": [], "assertions": []}},
            }
        ],
        "sideEffects": side_effects,
        "runtimeOutputs": [{"name": "createdProjectUrl", "source": "finalUrl", "publishAsNamedOutput": True}],
        "rerunPolicy": {"afterNoCommit": "allowed", "afterCommit": "allowed-with-new-inputs", "refreshRuntimeInputs": ["projectTitle"]},
        "sideEffectLifecycle": {"cleanupPolicy": "manual", "cleanupRequired": True, "instructions": "Delete the created project in the DB."},
        "resourceIdentity": {
            "resourceType": "collaboration-project",
            "identityStrategy": "generated-input",
            "identityInput": "projectTitle",
            "collisionPolicy": "allow-duplicates",
            "targetScope": "https://example.test",
            "confidence": "confirmed",
        },
    }


def test_implement_persist_migrates_unambiguous_legacy_rules(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("VERIFYSIGNAL_CORE_CMD", str(FAKE_CORE))
    create_write_policy_workspace(tmp_path)

    result = persist_stage(tmp_path, "implement", alias="add-collaboration-project", payload=_payload(legacy_rules_policy(mode="observe")))

    assert result["status"] == "persisted"
    side_effects = load_use_case(tmp_path, "add-collaboration-project").sideEffects
    assert side_effects["mode"] == "observe"
    assert "rules" not in side_effects
    assert side_effects["allowed"] == [{"id": "allow-backend-graphql", "kind": "network", "methods": ["POST"], "urlContains": "be.example.test/graphql"}]
    assert side_effects["forbidden"] == [{"id": "forbid-admin", "kind": "network", "methods": [], "urlContains": "/admin"}]
    assert "method" not in side_effects["allowed"][0]


def test_implement_persist_blocks_conflicting_legacy_and_canonical_policy(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("VERIFYSIGNAL_CORE_CMD", str(FAKE_CORE))
    create_write_policy_workspace(tmp_path)

    result = persist_stage(tmp_path, "implement", alias="add-collaboration-project", payload=_payload(conflicting_policy()))

    assert result["status"] == "invalid"
    assert result["blockers"][0]["code"] == "payload.invalid"
    assert "conflicting side-effect policy" in result["blockers"][0]["message"].lower()
