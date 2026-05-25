from __future__ import annotations

from proofsignal_spec.workflows.engine import classify_repair_stage


def test_repair_classification_matrix() -> None:
    assert classify_repair_stage({"message": "Expected product behavior is unclear"}) == "clarify"
    assert classify_repair_stage({"message": "Artifact plan picked wrong skill"}) == "plan"
    assert classify_repair_stage({"message": "Task fingerprint is stale"}) == "tasks"
    assert classify_repair_stage({"message": "Selector failed"}) == "implement"

