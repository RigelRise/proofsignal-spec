from __future__ import annotations

from .gate_coverage import missing_required_gate_contradictions
from .models import GateCoverageResult, PlannedValidationGate, RuntimeContradiction


def recommend_repairs_for_gate_coverage(
    gate_coverage: list[GateCoverageResult],
    planned_gates: list[PlannedValidationGate],
    *,
    source_run_id: str | None = None,
) -> list[RuntimeContradiction]:
    return missing_required_gate_contradictions(gate_coverage, planned_gates, source_run_id=source_run_id)


def proposals_from_contradictions(contradictions: list[RuntimeContradiction]) -> list[dict[str, str]]:
    proposals: list[dict[str, str]] = []
    for contradiction in contradictions:
        proposals.append(
            {
                "artifact": "planned validation gates",
                "field": contradiction.gateId,
                "reason": contradiction.observedEvidence,
                "expectedEffect": _expected_effect(contradiction.recommendation),
            }
        )
    return proposals


def _expected_effect(recommendation: str) -> str:
    if recommendation == "mark-conditional":
        return "Mark the gate conditional with an explicit condition and condition evaluation."
    if recommendation == "update-target-data":
        return "Update the target data or runtime assumptions so the planned gate exists."
    return "Replan the use case before weakening the browser validation skill."
