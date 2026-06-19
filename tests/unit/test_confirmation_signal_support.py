from __future__ import annotations

from tests.fixtures.workflows.side_effect_contract_alignment import supported_side_effect_contract, unsupported_dom_last_run

from proofsignal_spec.workflows.write_safety import confirmation_support_findings, effective_confirmation_support


def test_runtime_unsupported_confirmation_overrides_static_projection() -> None:
    support = effective_confirmation_support(
        "dom",
        core_contract=supported_side_effect_contract(static_dom_supported=True),
        runtime_outcomes=[unsupported_dom_last_run()],
    )

    assert support.staticSupport is True
    assert support.runtimeSupport is False
    assert support.effectiveSupport is False
    assert "unsupported-confirmation-signal" in support.evidence


def test_explicit_runtime_capability_restores_confirmation_support() -> None:
    support = effective_confirmation_support(
        "dom",
        core_contract=supported_side_effect_contract(runtime_dom_supported=True),
        runtime_outcomes=[unsupported_dom_last_run()],
    )

    assert support.staticSupport is True
    assert support.runtimeSupport is True
    assert support.effectiveSupport is True


def test_confirmation_support_findings_block_unsupported_declared_signal() -> None:
    findings = confirmation_support_findings(
        [{"id": "published-title-rendered", "type": "dom"}],
        core_contract=supported_side_effect_contract(),
        runtime_outcomes=[unsupported_dom_last_run()],
    )

    assert findings
    assert findings[0]["code"] == "unsupported-confirmation-signal"
    assert findings[0]["severity"] == "blocking"
