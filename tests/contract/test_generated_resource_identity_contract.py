from __future__ import annotations

from verifysignal_spec.workspace.models import ResolvedRuntimeBinding
from verifysignal_spec.workspace.repository import refresh_collision_findings

from tests.fixtures.workflows.write_rerun_identity import discarded_last_run, write_use_case_record


def test_generated_binding_contract_exposes_status_without_requiring_secret_values() -> None:
    binding = ResolvedRuntimeBinding(
        name="projectTitle",
        value="VerifySignal collab 123",
        source="generated",
        runId="run-1",
        useCaseAlias="add-collaboration-project",
        targetScope="https://example.test",
        refreshed=True,
        committed=True,
        status="committed",
    ).to_dict()

    assert binding["status"] == "committed"
    assert binding["committed"] is True
    assert "credential" not in binding


def test_discarded_generated_bindings_do_not_block_future_refreshes(tmp_path) -> None:
    write_use_case_record(
        tmp_path,
        last_run=discarded_last_run(value="VerifySignal collab seed stale"),
        resource_identity={
            "resourceType": "collaboration-project",
            "identityStrategy": "generated-input",
            "identityInput": "projectTitle",
            "collisionPolicy": "avoid",
            "targetScope": "https://example.test",
            "confidence": "confirmed",
        },
    )

    findings = refresh_collision_findings(
        tmp_path,
        use_case_alias="add-collaboration-project",
        target_scope="https://example.test",
        bindings={"projectTitle": "VerifySignal collab seed stale"},
    )

    assert findings == []
