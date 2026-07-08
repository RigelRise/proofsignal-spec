from __future__ import annotations

from verifysignal_spec.workspace.repository import committed_binding_values, refresh_collision_findings


def test_repeated_generated_value_blocks_with_ai_repairable_finding(tmp_path) -> None:
    from tests.fixtures.workflows.write_rerun_identity import committed_last_run, write_use_case_record

    write_use_case_record(tmp_path, last_run=committed_last_run(value="VerifySignal collab seed abcd12"))

    findings = refresh_collision_findings(
        tmp_path,
        use_case_alias="add-collaboration-project",
        target_scope="https://example.test",
        bindings={"projectTitle": "VerifySignal collab seed abcd12"},
    )

    assert findings
    assert findings[0]["code"] == "generated-binding-collision"
    assert findings[0]["repairability"] == "ai-repairable"


def test_committed_binding_lookup_is_scoped_by_use_case_and_target(tmp_path) -> None:
    from tests.fixtures.workflows.write_rerun_identity import committed_last_run, write_use_case_record

    write_use_case_record(tmp_path, last_run=committed_last_run(value="VerifySignal collab seed abcd12"))

    assert committed_binding_values(
        tmp_path,
        use_case_alias="add-collaboration-project",
        target_scope="https://example.test",
        binding_name="projectTitle",
    ) == {"VerifySignal collab seed abcd12"}
    assert committed_binding_values(
        tmp_path,
        use_case_alias="other-use-case",
        target_scope="https://example.test",
        binding_name="projectTitle",
    ) == set()


def test_collision_without_generation_context_requires_owner_action(tmp_path) -> None:
    from tests.fixtures.workflows.write_rerun_identity import committed_last_run, write_use_case_record

    last_run = committed_last_run(value="Repeated value")
    last_run["resolvedRuntimeInputs"][0]["name"] = "unknownBinding"
    write_use_case_record(tmp_path, last_run=last_run)

    findings = refresh_collision_findings(
        tmp_path,
        use_case_alias="add-collaboration-project",
        target_scope="https://example.test",
        bindings={"unknownBinding": "Repeated value"},
    )

    assert findings[0]["repairability"] == "owner-action-required"
    assert "suggestedReplacement" not in findings[0]
