from __future__ import annotations

from .gate_coverage import missing_required_gate_contradictions
from .models import GateCoverageResult, PlannedValidationGate, RepairRecommendation, RuntimeContradiction
from .repair_classification import classify_runtime_feedback


_RERUN_RESTRICTIVENESS = {
    "allowed": 0,
    "allowed-with-new-inputs": 1,
    "requires-confirmation": 2,
    "blocked": 3,
}


def combine_rerun_decision(core_risk: str | None, spec_decision: str | None) -> str:
    core_decision = _core_risk_to_spec_decision(core_risk)
    spec_decision = spec_decision or "blocked"
    if _RERUN_RESTRICTIVENESS.get(core_decision, 3) >= _RERUN_RESTRICTIVENESS.get(spec_decision, 3):
        return core_decision
    return spec_decision


def _core_risk_to_spec_decision(core_risk: str | None) -> str:
    mapping = {
        "safe": "allowed",
        "safe-with-new-inputs": "allowed-with-new-inputs",
        "requires-confirmation": "requires-confirmation",
        "blocked": "blocked",
    }
    return mapping.get(str(core_risk or "blocked"), "blocked")


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
                    autonomy="blocked" if category == "replan-required" else "confirmation-required",
                    safeMechanical=False,
                    intentPreserved=False,
                )
            )
            continue

        write_risk = _write_rerun_risk(finding, text)
        if write_risk:
            recommendations.append(
                RepairRecommendation(
                    id=f"repair-{index}-write-rerun-risk",
                    category="runtime-setup",
                    runtimeCategory="write-flow-safety",
                    summary=message or "The run may have crossed the write commit boundary.",
                    action="Review the created or affected resource before repair, cleanup, or rerun. Follow the explicit rerun policy and Core rerunRisk.",
                    affectedArtifacts=affected,
                    blockedReason=write_risk,
                    requiresUserDecision=True,
                    sourceFeedback=source_feedback,
                    autonomy="blocked",
                    safeMechanical=False,
                    intentPreserved=False,
                )
            )
            continue

        classified = classify_runtime_feedback(finding)
        if classified.category == "wait-flow-issue":
            recommendations.append(
                RepairRecommendation(
                    id=f"repair-{index}-wait-strategy",
                    category="safe-artifact-repair",
                    runtimeCategory=classified.category,
                    safeCategory="wait-strategy",
                    summary=classified.summary,
                    action=_safe_action("wait-strategy"),
                    affectedArtifacts=affected,
                    requiresUserDecision=False,
                    sourceFeedback=[*source_feedback, *classified.evidence],
                    autonomy="auto-applied",
                    safeMechanical=True,
                    intentPreserved=True,
                )
            )
            continue
        if classified.category == "selector-issue":
            recommendations.append(
                RepairRecommendation(
                    id=f"repair-{index}-selector-ambiguity",
                    category="safe-artifact-repair",
                    runtimeCategory=classified.category,
                    safeCategory="selector-ambiguity",
                    summary=classified.summary,
                    action=_safe_action("selector-ambiguity"),
                    affectedArtifacts=affected,
                    requiresUserDecision=False,
                    sourceFeedback=[*source_feedback, *classified.evidence],
                    autonomy="auto-applied",
                    safeMechanical=True,
                    intentPreserved=True,
                )
            )
            continue
        if classified.category == "coverage-mapping-issue":
            recommendations.append(
                RepairRecommendation(
                    id=f"repair-{index}-gateid-mapping",
                    category="safe-artifact-repair",
                    runtimeCategory=classified.category,
                    safeCategory="gateid-mapping",
                    summary=classified.summary,
                    action=_safe_action("gateid-mapping"),
                    affectedArtifacts=affected,
                    blockedReason=_confirmation_reason("gateid-mapping"),
                    requiresUserDecision=True,
                    sourceFeedback=[*source_feedback, *classified.evidence],
                    autonomy="confirmation-required",
                    safeMechanical=False,
                    intentPreserved=False,
                )
            )
            continue
        if classified.category == "execution-boundary-issue":
            recommendations.append(
                RepairRecommendation(
                    id=f"repair-{index}-skill-execution-boundary",
                    category="safe-artifact-repair",
                    runtimeCategory=classified.category,
                    safeCategory="main-skill-ordering",
                    summary=classified.summary,
                    action="Compose required helper behavior into the main skill or reclassify helper skills as source-only metadata; do not weaken required gates.",
                    affectedArtifacts=affected,
                    requiresUserDecision=False,
                    sourceFeedback=[*source_feedback, *classified.evidence],
                    autonomy="auto-applied",
                    safeMechanical=True,
                    intentPreserved=True,
                )
            )
            continue
        if classified.category in {"missing-prerequisite", "environment-recovery"}:
            recommendations.append(
                RepairRecommendation(
                    id=f"repair-{index}-{classified.category}",
                    category="runtime-setup",
                    runtimeCategory=classified.category,
                    summary=classified.summary,
                    action="Resolve the runtime environment or prerequisite, then rerun validation.",
                    affectedArtifacts=affected,
                    blockedReason=classified.summary,
                    requiresUserDecision=True,
                    sourceFeedback=[*source_feedback, *classified.evidence],
                    autonomy="confirmation-required",
                    safeMechanical=False,
                    intentPreserved=False,
                )
            )
            continue
        if classified.category == "data-product-state-issue":
            recommendations.append(
                RepairRecommendation(
                    id=f"repair-{index}-data-product-state",
                    category="clarification-required",
                    runtimeCategory=classified.category,
                    summary=classified.summary,
                    action="Return to clarification or planning before changing data assumptions or gate intent.",
                    affectedArtifacts=affected,
                    blockedReason="Data or product-state changes affect validation intent.",
                    requiresUserDecision=True,
                    sourceFeedback=[*source_feedback, *classified.evidence],
                    autonomy="confirmation-required",
                    safeMechanical=False,
                    intentPreserved=False,
                )
            )
            continue

        safe_category = _safe_category(text)
        if safe_category:
            requires_confirmation = safe_category in {"gateid-mapping"}
            recommendations.append(
                RepairRecommendation(
                    id=f"repair-{index}-{safe_category}",
                    category="safe-artifact-repair",
                    runtimeCategory=classified.category if classified.category != "unsupported-feedback" else None,
                    safeCategory=safe_category,  # type: ignore[arg-type]
                    summary=message or f"Runtime feedback indicates {safe_category}.",
                    action=_safe_action(safe_category),
                    affectedArtifacts=affected,
                    blockedReason=_confirmation_reason(safe_category) if requires_confirmation else None,
                    requiresUserDecision=requires_confirmation,
                    sourceFeedback=source_feedback,
                    autonomy="confirmation-required" if requires_confirmation else "auto-applied",
                    safeMechanical=not requires_confirmation,
                    intentPreserved=not requires_confirmation,
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
                autonomy="blocked",
                safeMechanical=False,
                intentPreserved=False,
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
    if any(term in text for term in ["skill-execution.", "execution-boundary", "source-only", "helper-skill"]):
        return "main-skill-ordering"
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
    if any(term in text for term in ["expected-behavior", "expected behavior", "product behavior"]):
        return ("clarification-required", "Repair changes expected product behavior and must be confirmed.")
    if any(term in text for term in ["credential", "password", "secret", "auth requirement"]):
        return ("clarification-required", "Repair changes credential requirements and must be confirmed.")
    if any(term in text for term in ["seeded-data", "data assumption", "data assumptions", "seeded state"]):
        return ("clarification-required", "Repair changes data assumptions and must be confirmed.")
    if any(term in text for term in ["hardcoded-profile", "fixed profile", "dynamic discovery", "replace dynamic"]):
        return ("clarification-required", "Repair changes a clarified runtime/data decision and must be re-clarified.")
    if any(term in text for term in ["weakened-gate", "tab-label-only", "navigation-only", "weaken required", "replace rendered"]):
        return ("replan-required", "Repair weakens required gate evidence and must be replanned.")
    return None


def _write_rerun_risk(finding: dict[str, object], text: str) -> str | None:
    classification = finding.get("resultClassification") if isinstance(finding.get("resultClassification"), dict) else {}
    side_effects = finding.get("sideEffects") if isinstance(finding.get("sideEffects"), dict) else {}
    side_effect_status = str(
        classification.get("sideEffectStatus")
        or finding.get("sideEffectStatus")
        or side_effects.get("status")
        or ""
    )
    failure_phase = str(classification.get("failurePhase") or finding.get("failurePhase") or side_effects.get("failurePhase") or "")
    rerun_risk = str(classification.get("rerunRisk") or finding.get("rerunRisk") or "")
    risky_statuses = {"possible", "likely-committed", "committed-confirmed", "violated", "unknown"}
    if side_effect_status in risky_statuses or failure_phase in {"post-commit", "post-verification"} or rerun_risk in {"requires-confirmation", "blocked"}:
        return "Public Core result indicates post-commit or uncertain mutating activity; blind repair-and-rerun is blocked."
    if any(term in text for term in ["post-commit", "committed-confirmed", "likely-committed", "side effect may", "mutating activity", "rerunrisk blocked"]):
        return "Runtime feedback indicates write-side-effect risk; blind repair-and-rerun is blocked."
    return None


def _safe_action(safe_category: str) -> str:
    actions = {
        "selector-ambiguity": "Auto-apply a stable selector specificity fix that preserves the same product behavior, then revalidate and rerun.",
        "wait-strategy": "Auto-apply a wait strategy adjustment that waits for rendered evidence, then revalidate and rerun.",
        "main-skill-ordering": "Pass and persist the planned main skill before helper skills.",
        "run-profile-defaults": "Apply observable debug/browser profile defaults without overriding user-specified pacing.",
        "gateid-mapping": "Ask for confirmation before changing coverage mapping, then map existing rendered-result evidence to the planned gateId if confirmed.",
    }
    return actions.get(safe_category, "Apply the safe mechanical repair and revalidate.")


def _confirmation_reason(safe_category: str) -> str:
    reasons = {
        "selector-ambiguity": "Selector changes can alter validation intent and require confirmation.",
        "wait-strategy": "Flow or wait-strategy changes can alter validation intent and require confirmation.",
        "gateid-mapping": "Coverage mapping changes can alter validation intent and require confirmation.",
    }
    return reasons.get(safe_category, "Repair requires confirmation.")
