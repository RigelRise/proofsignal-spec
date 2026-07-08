from __future__ import annotations

from verifysignal_spec.workflows.gates import gate_intent_from_plan, preserve_required_after_aborted_run, record_gate_intent_change


def test_gate_intent_state_lifecycle_preserves_required_after_aborted_run() -> None:
    state = gate_intent_from_plan({"id": "home-activity-slider", "required": True, "description": "Activity renders."})
    preserved = preserve_required_after_aborted_run(state, source_run_id="run-1")

    assert preserved.required is True
    assert preserved.changeSource == "plan"
    assert "aborted run" in preserved.changeReason


def test_gate_intent_requiredness_change_requires_explicit_source() -> None:
    state = gate_intent_from_plan({"id": "about-tab-content", "required": True})
    changed = record_gate_intent_change(
        state,
        required=False,
        condition="Profile has About tab",
        source="repair-confirmation",
        reason="Developer explicitly confirmed conditional behavior.",
    )

    assert changed.required is False
    assert changed.conditionStatus == "unknown"
    assert changed.changeSource == "repair-confirmation"
