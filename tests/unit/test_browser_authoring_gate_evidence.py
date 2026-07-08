from __future__ import annotations

from verifysignal_spec.workflows.browser_authoring import validate_browser_payload
from verifysignal_spec.workflows.evidence import extract_browser_evidence


def test_browser_authoring_allows_gate_id_and_operation_name_metadata() -> None:
    browser = {
        "targets": {"profileName": {"css": "h2", "domainSemantics": "Profile name"}},
        "steps": [
            {
                "id": "profile-query",
                "action": "awaitNetwork",
                "gateId": "overview-profile-query",
                "match": {"method": "POST", "urlContains": "graphql", "status": 200, "operationName": "ProfileQuery"},
            }
        ],
        "assertions": [{"id": "profile-name", "kind": "visible", "target": "profileName", "gateId": "overview-data-card"}],
    }

    assert validate_browser_payload(browser) == []
    evidence = extract_browser_evidence(browser, known_gate_ids={"overview-data-card", "overview-profile-query"})
    assert evidence.uiAssertions[0].gateId == "overview-data-card"
    assert evidence.networkChecks[0].operationName == "ProfileQuery"


def test_body_text_is_reported_as_weak_rendered_evidence() -> None:
    browser = {
        "targets": {"pageBody": {"css": "body", "domainSemantics": "Whole page body"}},
        "steps": [{"id": "body-text", "action": "checkText", "target": "pageBody", "value": "Jordan", "gateId": "overview-data-card"}],
    }

    evidence = extract_browser_evidence(browser, known_gate_ids={"overview-data-card"})

    assert evidence.uiAssertions
    assert evidence.warnings
