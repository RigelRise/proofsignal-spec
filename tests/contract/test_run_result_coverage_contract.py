from __future__ import annotations

from proofsignal_spec.workflows.evidence import normalize_planned_gates
from proofsignal_spec.workflows.gate_coverage import calculate_gate_coverage, coverage_status
from proofsignal_spec.workflows.models import EvidenceInventory
from proofsignal_spec.workflows.repair_recommendations import recommend_repairs_for_gate_coverage


def test_core_pass_with_missing_required_gate_is_incomplete() -> None:
    gates, _warnings = normalize_planned_gates([{"id": "about-tab-content", "description": "About tab content", "required": True}])
    coverage = calculate_gate_coverage(gates, EvidenceInventory())

    assert coverage_status("passed", coverage) == "incomplete"
    contradictions = recommend_repairs_for_gate_coverage(coverage, gates, source_run_id="run-1")
    assert contradictions[0].gateId == "about-tab-content"
    assert contradictions[0].recommendation == "mark-conditional"


def test_conditional_unmet_gate_does_not_make_run_incomplete() -> None:
    gates, _warnings = normalize_planned_gates(
        [
            {
                "id": "about-tab-content",
                "description": "About tab",
                "required": False,
                "condition": "Profile has About tab",
                "conditionEvaluation": "unmet",
            }
        ]
    )
    coverage = calculate_gate_coverage(gates, EvidenceInventory())

    assert coverage[0].status == "conditional-unmet"
    assert coverage_status("passed", coverage) == "complete"
