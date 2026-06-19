from __future__ import annotations

from proofsignal_spec.workspace.models import ResolvedRuntimeBinding


def test_generated_binding_contract_exposes_status_without_requiring_secret_values() -> None:
    binding = ResolvedRuntimeBinding(
        name="projectTitle",
        value="ProofSignal collab 123",
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
