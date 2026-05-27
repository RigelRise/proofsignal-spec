from __future__ import annotations

from .gate_coverage import missing_required_gate_contradictions
from .models import GateCoverageResult, PlannedValidationGate, RepairRecommendation, RuntimeContradiction


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


def classify_repair_findings(findings: list[dict[str, object]]) -> list[RepairRecommendation]:
    recommendations: list[RepairRecommendation] = []
    for index, finding in enumerate(findings, start=1):
        code = str(finding.get("code") or "")
        message = str(finding.get("message") or finding.get("reason") or "")
        text = f"{code} {message}".lower()
        artifact = str(finding.get("artifact") or "").strip()
        path = str(finding.get("path") or "").strip()
        affected = [item for item in [artifact] if item]
        source_feedback = [item for item in [code or f"finding-{index}", path] if item]

        blocked_category = _blocked_category(text)
        if blocked_category:
            category, reason = blocked_category
            recommendations.append(
                RepairRecommendation(
                    id=f"repair-{index}-{category}",
                    category=category,  # type: ignore[arg-type]
                    summary=message or "Repair would change the approved validation intent.",
                    action="Return to clarification or planning before changing this behavior.",
                    affectedArtifacts=affected,
                    blockedReason=reason,
                    requiresUserDecision=True,
                    sourceFeedback=source_feedback,
                )
            )
            continue

        safe_category = _safe_category(text)
        if safe_category:
            recommendations.append(
                RepairRecommendation(
                    id=f"repair-{index}-{safe_category}",
                    category="safe-artifact-repair",
                    safeCategory=safe_category,  # type: ignore[arg-type]
                    summary=message or f"Runtime feedback indicates {safe_category}.",
                    action=_safe_action(safe_category),
                    affectedArtifacts=affected,
                    requiresUserDecision=False,
                    sourceFeedback=source_feedback,
                )
            )
            continue

        recommendations.append(
            RepairRecommendation(
                id=f"repair-{index}-unsupported",
                category="unsupported",
                summary=message or "Runtime feedback is not in a supported safe repair category.",
                action="Inspect manually and replan if this changes the use case.",
                affectedArtifacts=affected,
                blockedReason="Unsupported runtime feedback cannot be auto-applied.",
                requiresUserDecision=True,
                sourceFeedback=source_feedback,
            )
        )
    return recommendations


def _expected_effect(recommendation: str) -> str:
    if recommendation == "mark-conditional":
        return "Mark the gate conditional with an explicit condition and condition evaluation."
    if recommendation == "update-target-data":
        return "Update the target data or runtime assumptions so the planned gate exists."
    return "Replan the use case before weakening the browser validation skill."


def _safe_category(text: str) -> str | None:
    if any(term in text for term in ["strict-mode", "strict mode", "multiple elements", "selector ambiguity", "locator matched", "resolved to", "selector did not match", "did not match"]):
        return "selector-ambiguity"
    if any(term in text for term in ["wait-timeout", "timeout", "timed out", "wait strategy", "client-side graphql", "ssr"]):
        return "wait-strategy"
    if any(term in text for term in ["main-skill", "main skill", "helper before main", "helper skill executed"]):
        return "main-skill-ordering"
    if any(term in text for term in ["slowmo", "slow-mo", "slow motion", "run-profile", "debug run"]):
        return "run-profile-defaults"
    if any(term in text for term in ["gateid", "gate id", "gate mapping", "missing gate", "lacks gate"]):
        return "gateid-mapping"
    return None


def _blocked_category(text: str) -> tuple[str, str] | None:
    if any(term in text for term in ["hardcoded-profile", "fixed profile", "dynamic discovery", "replace dynamic"]):
        return ("clarification-required", "Repair changes a clarified runtime/data decision and must be re-clarified.")
    if any(term in text for term in ["weakened-gate", "tab-label-only", "navigation-only", "weaken required", "replace rendered"]):
        return ("replan-required", "Repair weakens required gate evidence and must be replanned.")
    return None


def _safe_action(safe_category: str) -> str:
    actions = {
        "selector-ambiguity": "Narrow the target selector to a stable unique element without changing the gate intent.",
        "wait-strategy": "Replace brittle waits with a DOM/rendered-result wait appropriate for the page lifecycle.",
        "main-skill-ordering": "Pass and persist the planned main skill before helper skills.",
        "run-profile-defaults": "Apply observable debug/browser profile defaults without overriding user-specified pacing.",
        "gateid-mapping": "Map existing rendered-result evidence to the planned gateId or add equivalent evidence.",
    }
    return actions.get(safe_category, "Apply the safe mechanical repair and revalidate.")
