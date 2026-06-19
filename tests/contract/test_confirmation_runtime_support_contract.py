from __future__ import annotations

from tests.fixtures.workflows.side_effect_contract_alignment import supported_side_effect_contract, unsupported_dom_last_run

from proofsignal_spec.workflows.write_safety import confirmation_support_findings


def test_effective_confirmation_support_uses_runtime_outcome_as_stronger_public_signal() -> None:
    findings = confirmation_support_findings(
        [{"id": "rendered-title", "type": "dom"}, {"id": "created-url", "type": "runtimeOutput"}],
        core_contract=supported_side_effect_contract(static_dom_supported=True),
        runtime_outcomes=[unsupported_dom_last_run()],
    )

    assert [item["signalType"] for item in findings] == ["dom"]
    assert "runtime outcome" in findings[0]["message"].lower()


def test_newer_public_runtime_capability_data_can_prove_support() -> None:
    findings = confirmation_support_findings(
        [{"id": "rendered-title", "type": "dom"}],
        core_contract=supported_side_effect_contract(runtime_dom_supported=True),
        runtime_outcomes=[unsupported_dom_last_run()],
    )

    assert findings == []
