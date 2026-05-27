from __future__ import annotations

from proofsignal_spec.workflows.evidence import normalize_planned_gates
from proofsignal_spec.workflows.gate_coverage import calculate_gate_coverage
from proofsignal_spec.workflows.models import EvidenceInventory
from proofsignal_spec.workflows.repair_recommendations import classify_repair_findings, proposals_from_contradictions, recommend_repairs_for_gate_coverage


def test_runtime_contradiction_proposes_replan_options_without_mutating_artifacts() -> None:
    gates, _warnings = normalize_planned_gates([{"id": "projects-tab-content", "description": "Projects tab", "required": True}])
    coverage = calculate_gate_coverage(gates, EvidenceInventory())

    contradictions = recommend_repairs_for_gate_coverage(coverage, gates, source_run_id="run-1")
    proposals = proposals_from_contradictions(contradictions)

    assert contradictions[0].expectedEvidence == "Projects tab"
    assert proposals[0]["expectedEffect"]
    assert "weaken" in proposals[0]["expectedEffect"].lower() or "conditional" in proposals[0]["expectedEffect"].lower()


def test_weakened_gate_repairs_are_replan_required() -> None:
    recommendations = classify_repair_findings(
        [
            {"code": "weakened-gate", "message": "Replace rendered tab assertion with tab-label-only check."},
            {"code": "navigation-only-replacement", "message": "Replace profile content gate with URL navigation only."},
        ]
    )

    assert [item.category for item in recommendations] == ["replan-required", "replan-required"]
    assert all(item.requiresUserDecision for item in recommendations)
    assert all(item.blockedReason for item in recommendations)


def test_selector_flow_and_coverage_repairs_require_confirmation() -> None:
    recommendations = classify_repair_findings(
        [
            {"code": "strict-mode-violation", "message": "locator resolved to multiple elements"},
            {"code": "wait-timeout", "message": "wait strategy timed out after changing the page flow"},
            {"code": "missing-gateid", "message": "coverage gate mapping is missing"},
        ]
    )

    assert [item.safeCategory for item in recommendations] == ["selector-ambiguity", "wait-strategy", "gateid-mapping"]
    assert all(item.requiresUserDecision for item in recommendations)
    assert all(item.blockedReason for item in recommendations)


def test_deterministic_contract_and_metadata_repairs_remain_auto_repairable() -> None:
    recommendations = classify_repair_findings(
        [
            {"code": "main-skill-ordering", "message": "helper skill executed before main skill"},
            {"code": "debug-slowmo-default", "message": "debug run has slowMoMs 0"},
        ]
    )

    assert [item.safeCategory for item in recommendations] == ["main-skill-ordering", "run-profile-defaults"]
    assert all(not item.requiresUserDecision for item in recommendations)
