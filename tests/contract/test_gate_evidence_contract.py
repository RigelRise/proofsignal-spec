from __future__ import annotations

from proofsignal_spec.workflows.evidence import extract_browser_evidence, normalize_planned_gates
from proofsignal_spec.workflows.gate_coverage import calculate_gate_coverage

from tests.fixtures.workflows.real_run_guardrails import coherent_profile_skill, profile_validation_gates


def test_gate_evidence_requires_explicit_gate_id() -> None:
    browser = coherent_profile_skill()["browser"]
    browser["assertions"].append({"id": "unmapped", "kind": "visible", "target": "profileName"})

    gates, warnings = normalize_planned_gates(profile_validation_gates())
    evidence = extract_browser_evidence(browser, known_gate_ids={gate.id for gate in gates})
    coverage = calculate_gate_coverage(gates, evidence)

    assert not warnings
    assert evidence.unmappedEvidence
    assert next(item for item in coverage if item.gateId == "overview-data-card").status == "exercised"


def test_conditional_gate_without_evaluation_is_not_evaluated() -> None:
    gates, _warnings = normalize_planned_gates(
        [{"id": "about-tab-content", "description": "About tab", "required": False, "condition": "Profile has About tab"}]
    )
    coverage = calculate_gate_coverage(gates, extract_browser_evidence({"targets": {}, "steps": [], "assertions": []}))

    assert coverage[0].status == "not-evaluated"


def test_network_operation_name_is_metadata_only() -> None:
    browser = {
        "targets": {},
        "steps": [
            {
                "id": "network",
                "action": "awaitNetwork",
                "gateId": "overview-profile-query",
                "match": {"method": "POST", "operationName": "ProfileQuery", "status": 200},
            }
        ],
    }
    gates, _warnings = normalize_planned_gates([{"id": "overview-profile-query", "description": "Profile query"}])

    evidence = extract_browser_evidence(browser, known_gate_ids={gate.id for gate in gates})

    assert evidence.networkChecks[0].operationName == "ProfileQuery"
    assert evidence.blockers
    assert "public match pattern" in evidence.blockers[0]
