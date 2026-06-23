from __future__ import annotations

import json

from proofsignal_spec.commands import policy as policy_command
from proofsignal_spec.workspace.repository import load_use_case
from tests.fixtures.workflows.live_write_readiness import create_live_write_readiness_workspace


def test_policy_set_class_none_updates_record_and_run_request_without_touching_params(tmp_path) -> None:
    # Tier-2: declare a use case read-only WITHOUT round-tripping the implement payload (the
    # all-or-nothing path that caused Bug 2). Params/skills/inputs must be preserved.
    create_live_write_readiness_workspace(tmp_path)

    result = policy_command.set_policy(tmp_path, "add-collaboration-project", side_effect_class="none")

    assert result["status"] == "persisted", result
    record = load_use_case(tmp_path, "add-collaboration-project")
    assert record.sideEffects["class"] == "none"
    # runtimeInputs preserved (no skill round-trip)
    assert [item.name for item in record.runtimeInputs] == ["baseUrl", "resourceName"]
    # run-request re-synced so a later `run` honors the new class, AND parameters preserved
    run_request = json.loads((tmp_path / ".proofsignal/run-requests/add-collaboration-project.yaml").read_text())
    assert run_request["sideEffectPolicy"]["class"] == "none"
    assert run_request["parameters"]["baseUrl"] == "https://example.test"


def test_policy_set_preserves_existing_allowed_rules(tmp_path) -> None:
    create_live_write_readiness_workspace(tmp_path)

    policy_command.set_policy(tmp_path, "add-collaboration-project", side_effect_class="none", mode="observe")

    record = load_use_case(tmp_path, "add-collaboration-project")
    assert record.sideEffects["class"] == "none"
    assert record.sideEffects["mode"] == "observe"
    # the prior allowed[] rule (graphql write) is preserved, not wiped
    assert any(rule.get("id") == "create-project" for rule in record.sideEffects.get("allowed", []))


def test_policy_set_class_write_without_resource_identity_blocks(tmp_path) -> None:
    create_live_write_readiness_workspace(tmp_path)
    # about-page-unauth is class:none with no resourceIdentity; promoting it to write must block.
    result = policy_command.set_policy(tmp_path, "about-page-unauth", side_effect_class="write")
    assert result["status"] == "blocked", result


def test_policy_set_via_cli(tmp_path, capsys) -> None:
    from proofsignal_spec.cli import main

    create_live_write_readiness_workspace(tmp_path)
    code = main(["policy", "set", "add-collaboration-project", "--class", "none", "--project", str(tmp_path), "--json"])

    assert code == 0
    out = capsys.readouterr().out
    assert json.loads(out)["sideEffects"]["class"] == "none"
