from __future__ import annotations

from proofsignal_spec.workflows.evidence import extract_browser_evidence, normalize_planned_gates
from proofsignal_spec.workflows.gate_coverage import calculate_gate_coverage, coverage_status


def test_required_page_result_gate_without_ui_evidence_is_network_only() -> None:
    gates, _warnings = normalize_planned_gates([{"id": "profile-card", "description": "Profile data card renders"}])
    evidence = extract_browser_evidence(
        {
            "steps": [
                {
                    "id": "network",
                    "action": "awaitNetwork",
                    "gateId": "profile-card",
                    "match": {"method": "POST", "urlContains": "graphql", "status": 200},
                }
            ]
        },
        known_gate_ids={"profile-card"},
    )

    coverage = calculate_gate_coverage(gates, evidence)

    assert coverage[0].status == "network-only"
    assert coverage_status("passed", coverage) == "incomplete"


def test_backend_gate_with_network_evidence_is_exercised() -> None:
    gates, _warnings = normalize_planned_gates([{"id": "profile-query", "description": "Profile backend query"}])
    evidence = extract_browser_evidence(
        {
            "steps": [
                {
                    "id": "network",
                    "action": "awaitNetwork",
                    "gateId": "profile-query",
                    "match": {"method": "POST", "urlContains": "graphql", "status": 200},
                }
            ]
        },
        known_gate_ids={"profile-query"},
    )

    coverage = calculate_gate_coverage(gates, evidence)

    assert coverage[0].status == "exercised"


def test_required_gate_with_ui_evidence_is_exercised() -> None:
    gates, _warnings = normalize_planned_gates([{"id": "profile-name", "description": "Profile name"}])
    evidence = extract_browser_evidence(
        {
            "targets": {"profileName": {"css": "h2", "domainSemantics": "Profile name"}},
            "assertions": [{"id": "assert-name", "kind": "visible", "target": "profileName", "gateId": "profile-name"}],
        },
        known_gate_ids={"profile-name"},
    )

    coverage = calculate_gate_coverage(gates, evidence)

    assert coverage[0].status == "exercised"
    assert coverage_status("passed", coverage) == "complete"
