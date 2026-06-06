from __future__ import annotations

from proofsignal_spec.core.executable_contract import project_core_contract
from proofsignal_spec.workflows.evidence import extract_browser_evidence, extract_core_runtime_evidence
from tests.fixtures.managed_runtime import core_contract_fixture_payload


def test_runtime_report_coverage_uses_core_declared_report_sections() -> None:
    projection = project_core_contract(
        core_contract_fixture_payload(
            extra_sections={
                "reportCoverage": {
                    "schemaVersion": "qa-report/v2",
                    "gateIdFields": ["gate"],
                    "stepCollections": ["actions"],
                    "evidenceCollections": ["artifacts"],
                }
            }
        )
    )
    result = {
        "data": {
            "report": {
                "schemaVersion": "qa-report/v2",
                "actions": [
                    {
                        "id": "publish",
                        "status": "passed",
                        "gate": "project-page-renders",
                        "artifacts": [{"id": "publish-shot", "source": "screenshot", "status": "passed"}],
                    }
                ],
            }
        }
    }

    inventory = extract_core_runtime_evidence(result, known_gate_ids={"project-page-renders"}, core_contract=projection)

    assert [item.gateId for item in inventory.uiAssertions] == ["project-page-renders"]
    assert [item.gateId for item in inventory.screenshots] == ["project-page-renders"]


def test_browser_network_evidence_uses_core_declared_match_keys() -> None:
    projection = project_core_contract(
        core_contract_fixture_payload(
            extra_sections={
                "browserWorkflow": {
                    "actions": [{"name": "awaitNetwork", "status": "stable", "requiredFields": ["match"]}],
                    "assertions": [{"name": "visible", "status": "stable", "requiredFields": ["target"]}],
                    "targetSignals": [{"name": "testId", "status": "stable"}],
                    "networkMatchKeys": [{"name": "urlPattern", "status": "stable"}],
                    "metadataKeys": [{"name": "method", "status": "stable"}, {"name": "expectedStatus", "status": "stable"}],
                }
            }
        )
    )
    browser = {
        "steps": [
            {
                "id": "wait-publish",
                "action": "awaitNetwork",
                "gateId": "project-publish-mutation",
                "match": {"method": "POST", "urlPattern": "/graphql", "expectedStatus": 200},
            }
        ]
    }

    inventory = extract_browser_evidence(browser, known_gate_ids={"project-publish-mutation"}, core_contract=projection)

    assert inventory.blockers == []
    assert inventory.networkChecks[0].publicMatchKeys == ["urlPattern"]
