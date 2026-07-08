from __future__ import annotations

from .models import EvidenceInventory, GateCoverageResult, PlannedValidationGate, RuntimeContradiction


def calculate_gate_coverage(gates: list[PlannedValidationGate], evidence: EvidenceInventory) -> list[GateCoverageResult]:
    coverage: list[GateCoverageResult] = []
    ui_by_gate = _group([item for item in evidence.uiAssertions], "gateId")
    network_by_gate = _group([item for item in evidence.networkChecks], "gateId")
    screenshots_by_gate = _group([item for item in evidence.screenshots], "gateId")

    for gate in gates:
        ui_ids = [item.id for item in ui_by_gate.get(gate.id, [])]
        network_ids = [item.id for item in network_by_gate.get(gate.id, [])]
        screenshot_ids = [item.id for item in screenshots_by_gate.get(gate.id, [])]
        status = _status_for_gate(gate, ui_ids, network_ids, screenshot_ids)
        notes = _notes_for_status(status)
        coverage.append(
            GateCoverageResult(
                gateId=gate.id,
                status=status,
                condition=gate.condition,
                conditionEvaluation=gate.conditionEvaluation,
                uiEvidenceIds=ui_ids,
                networkEvidenceIds=network_ids,
                screenshotEvidenceIds=screenshot_ids,
                notes=notes,
                required=gate.required,
                missingEvidence=_missing_evidence_for_status(status),
            )
        )
    return coverage


def coverage_status(core_status: str, gate_coverage: list[GateCoverageResult]) -> str:
    if core_status in {"failed", "error"}:
        return "diagnostic"
    if core_status == "blocked":
        return "blocked"
    incomplete = {"missing", "network-only", "screenshot-only", "unmapped", "not-evaluated", "incomplete"}
    if any(item.required and item.status in incomplete for item in gate_coverage):
        return "incomplete"
    return "complete"


def missing_required_gate_contradictions(
    gate_coverage: list[GateCoverageResult],
    gates: list[PlannedValidationGate],
    *,
    source_run_id: str | None = None,
) -> list[RuntimeContradiction]:
    gates_by_id = {gate.id: gate for gate in gates}
    contradictions: list[RuntimeContradiction] = []
    for item in gate_coverage:
        gate = gates_by_id.get(item.gateId)
        if not gate or not gate.required:
            continue
        if item.status not in {"missing", "network-only", "screenshot-only", "not-evaluated"}:
            continue
        recommendation = "mark-conditional" if item.status == "missing" else "replan"
        contradictions.append(
            RuntimeContradiction(
                id=f"contradiction-{item.gateId}",
                gateId=item.gateId,
                expectedEvidence=gate.description or item.gateId,
                observedEvidence=item.notes or f"Gate {item.gateId} did not have complete rendered-result evidence.",
                recommendation=recommendation,
                sourceRunId=source_run_id,
            )
        )
    return contradictions


def _status_for_gate(gate: PlannedValidationGate, ui_ids: list[str], network_ids: list[str], screenshot_ids: list[str]) -> str:
    if gate.condition:
        if gate.conditionEvaluation == "unmet":
            return "conditional-unmet"
        if gate.conditionEvaluation == "met":
            return "conditional-met" if ui_ids else "missing"
        return "not-evaluated"
    if ui_ids:
        return "exercised"
    if network_ids and _network_only_satisfies_gate(gate):
        return "exercised"
    if network_ids:
        return "network-only"
    if screenshot_ids:
        return "screenshot-only"
    return "missing"


def _network_only_satisfies_gate(gate: PlannedValidationGate) -> bool:
    text = f"{gate.id} {gate.description}".lower()
    return any(term in text for term in ["backend", "network", "request", "query", "graphql", "api"])


def _notes_for_status(status: str) -> str | None:
    if status == "missing":
        return "No mapped evidence was found for this planned gate."
    if status == "network-only":
        return "Network evidence exists, but no rendered-result UI assertion proves the page result."
    if status == "screenshot-only":
        return "Screenshot evidence exists, but screenshots do not replace a specific rendered-result assertion."
    if status == "not-evaluated":
        return "Conditional gate had no condition evaluation for this run."
    return None


def _missing_evidence_for_status(status: str) -> list[str]:
    if status == "missing":
        return ["mapped rendered-result evidence"]
    if status == "network-only":
        return ["mapped rendered-result UI assertion"]
    if status == "screenshot-only":
        return ["mapped rendered-result assertion"]
    if status == "not-evaluated":
        return ["condition evaluation"]
    if status == "incomplete":
        return ["required gate evidence"]
    return []


def _group(items: list[object], field: str) -> dict[str, list[object]]:
    grouped: dict[str, list[object]] = {}
    for item in items:
        key = getattr(item, field, None)
        if key:
            grouped.setdefault(str(key), []).append(item)
    return grouped
