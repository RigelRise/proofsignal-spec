from __future__ import annotations

from proofsignal_spec.workspace.models import ResolvedRuntimeBinding


def test_resolved_binding_supports_prepared_committed_and_discarded_status() -> None:
    prepared = ResolvedRuntimeBinding(name="projectTitle", value="ProofSignal A", status="prepared")
    committed = ResolvedRuntimeBinding.from_dict({"name": "projectTitle", "value": "ProofSignal B", "committed": True})
    discarded = ResolvedRuntimeBinding.from_dict({"name": "projectTitle", "value": "ProofSignal C", "status": "discarded"})

    assert prepared.to_dict()["status"] == "prepared"
    assert committed.status == "committed"
    assert committed.to_dict()["committed"] is True
    assert discarded.status == "discarded"
    assert discarded.to_dict()["committed"] is False
