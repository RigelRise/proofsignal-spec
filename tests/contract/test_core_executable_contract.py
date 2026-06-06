from __future__ import annotations

import os

from helpers import FAKE_CORE
from proofsignal_spec.core.adapter import CoreAdapter


def test_core_adapter_invokes_public_contracts_operation() -> None:
    result = CoreAdapter(executable=str(FAKE_CORE)).contracts()

    assert result["schema"] == "proofsignal.contracts/v1"
    assert result["operation"] == "contracts"
    assert result["status"] == "passed"
    assert "browserWorkflow" in result["data"]
    assert "credentialSyntax" in result["data"]["placeholders"]


def test_core_contract_projection_exposes_run_request_and_skill_sections() -> None:
    from proofsignal_spec.core.executable_contract import project_core_contract

    raw = CoreAdapter(executable=str(FAKE_CORE)).contracts()
    projection = project_core_contract(raw, runtime_identity=str(FAKE_CORE), core_version="0.1.0")

    assert projection["source"] == "core-public-contract"
    assert projection["sections"]["runRequest"]["schemaVersion"] == "qa-run-request/v1"
    assert projection["sections"]["skill"]["schemaVersion"] == "proofsignal-browser-skill/v1"
    assert "navigate" in projection["sections"]["browserWorkflow"]["validActions"]
    assert "dragAndDrop" not in projection["sections"]["browserWorkflow"]["validActions"]


def test_core_contract_projection_filters_experimental_items() -> None:
    from proofsignal_spec.core.executable_contract import project_core_contract

    old_mode = os.environ.get("FAKE_PROOFSIGNAL_MODE")
    os.environ["FAKE_PROOFSIGNAL_MODE"] = "experimental-contract"
    try:
        raw = CoreAdapter(executable=str(FAKE_CORE)).contracts()
    finally:
        if old_mode is None:
            os.environ.pop("FAKE_PROOFSIGNAL_MODE", None)
        else:
            os.environ["FAKE_PROOFSIGNAL_MODE"] = old_mode

    projection = project_core_contract(raw, runtime_identity=str(FAKE_CORE), core_version="0.1.0")

    browser = projection["sections"]["browserWorkflow"]
    assert "dragAndDrop" not in browser["validActions"]
    assert any(item["name"] == "dragAndDrop" for item in browser["experimentalItems"]["actions"])
