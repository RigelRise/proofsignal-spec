from __future__ import annotations

from verifysignal_spec.workspace.models import ResolvedRuntimeBinding


def test_resolved_generated_binding_serializes_without_credential_values() -> None:
    binding = ResolvedRuntimeBinding(
        name="projectTitle",
        value="VerifySignal collab seed abc123",
        source="generated",
        runId="run-1",
        useCaseAlias="add-collaboration-project",
        targetScope="https://app.example.test",
        refreshed=True,
        committed=False,
    )

    data = binding.to_dict()

    assert data["value"] == "VerifySignal collab seed abc123"
    assert "credential" not in data
