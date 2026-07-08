from __future__ import annotations

from tests.fixtures.managed_runtime import current_core_contract_fixture_payload
from verifysignal_spec.core.executable_contract import project_core_contract, side_effect_guardrails_projection


def test_core_projection_exposes_side_effect_guardrails() -> None:
    projection = project_core_contract(current_core_contract_fixture_payload())
    guardrails = projection["sections"]["sideEffectGuardrails"]

    assert guardrails["status"] == "supported"
    assert "write" in guardrails["policyClasses"]
    assert "enforce" in guardrails["policyModes"]
    assert "finalUrl" in guardrails["confirmationSignalTypes"]
    assert "safe-with-new-inputs" in guardrails["rerunRisks"]


def test_side_effect_projection_reports_missing_guardrails() -> None:
    projection = project_core_contract(current_core_contract_fixture_payload(extra_sections={"sideEffectGuardrails": None}))

    guardrails = side_effect_guardrails_projection(projection)

    assert guardrails["supported"] is False
    assert guardrails["finding"]["code"] == "side-effect-core-contract-missing"

