from __future__ import annotations

from verifysignal_spec.workspace.models import UnderstandingFreshnessState


def test_stale_inventory_context_blocks_for_refresh() -> None:
    state = UnderstandingFreshnessState.from_context(
        stale=True,
        workflow_context="specify",
        reasons=["understanding older than threshold"],
    )

    assert state.status == "stale"
    assert state.policy == "block"
    assert state.recommendedAction == "refresh-understanding"


def test_alias_scoped_read_only_run_warns_when_impact_is_unaffected() -> None:
    state = UnderstandingFreshnessState.from_context(
        stale=True,
        workflow_context="run",
        use_case_impact="unaffected",
        side_effect_class="none",
    )

    assert state.policy == "warn"
    assert state.recommendedAction == "continue"


def test_alias_scoped_write_run_requires_confirmation_when_impact_unknown() -> None:
    state = UnderstandingFreshnessState.from_context(
        stale=True,
        workflow_context="run",
        use_case_impact="unknown",
        side_effect_class="write",
    )

    assert state.policy == "requires-confirmation"
    assert state.recommendedAction == "confirm"


def test_alias_scoped_affected_run_requires_validation_not_understand() -> None:
    state = UnderstandingFreshnessState.from_context(
        stale=True,
        workflow_context="run",
        use_case_impact="affected",
        side_effect_class="write",
    )

    assert state.policy == "block"
    assert state.recommendedAction == "validate"
