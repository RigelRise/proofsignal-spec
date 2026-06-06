from __future__ import annotations

from tests.fixtures.managed_runtime import core_contract_fixture_payload
from proofsignal_spec.workflows.browser_authoring import browser_authoring_contract
from proofsignal_spec.core.executable_contract import project_core_contract


def test_projection_filters_to_stable_browser_authoring_items() -> None:
    payload = core_contract_fixture_payload(
        browser_actions=[
            {"name": "navigate", "status": "stable", "requiredFields": ["value"]},
            {"name": "press", "status": "stable", "requiredFields": ["target", "value"]},
            {"name": "dragAndDrop", "status": "experimental", "requiredFields": ["target", "value"]},
        ]
    )

    projection = project_core_contract(payload, runtime_identity="fake-core", core_version="0.1.0")
    browser = projection["sections"]["browserWorkflow"]

    assert browser["validActions"] == ["navigate", "press"]
    assert browser["experimentalItems"]["actions"][0]["name"] == "dragAndDrop"
    authoring = browser_authoring_contract(core_contract=projection)
    assert "dragAndDrop" not in authoring["validActions"]
    assert authoring["experimentalItems"]["actions"][0]["name"] == "dragAndDrop"
    assert projection["sections"]["runRequest"]["schemaVersion"] == "qa-run-request/v1"
    assert projection["sections"]["skill"]["schemaVersion"] == "proofsignal-browser-skill/v1"


def test_projection_preserves_required_contract_sections() -> None:
    payload = core_contract_fixture_payload()

    projection = project_core_contract(payload)

    assert set(projection["sections"]) == {
        "operations",
        "runRequest",
        "skill",
        "browserWorkflow",
        "credentials",
        "placeholders",
        "reportCoverage",
        "publicRedactionPolicy",
        "runtimeTrustHandoff",
    }
    assert "environment" in projection["sections"]["credentials"]["sourceNames"]
    assert projection["sections"]["placeholders"]["credentialSyntax"] == "{{credentials.<group>.<field>}}"
