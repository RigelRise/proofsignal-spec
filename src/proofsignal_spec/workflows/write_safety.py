from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from proofsignal_spec.workspace.models import ConfirmationSignalSupport, PolicyCompatibilityFinding, RerunPolicy
from proofsignal_spec.workflows.repair_recommendations import combine_rerun_decision


def normalize_side_effect_policy(policy: dict[str, Any] | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return Core-runtime-compatible side-effect policy plus compatibility findings.

    Legacy Spec artifacts used sideEffectPolicy.rules[].effect/match. Core runtime
    consumes sideEffectPolicy.allowed[] and sideEffectPolicy.forbidden[] with match
    keys at the rule top level. This helper accepts the legacy shape only as an
    input compatibility format and never emits `rules`.
    """

    if not isinstance(policy, dict):
        return {}, []

    canonical = {key: value for key, value in policy.items() if key != "rules"}
    findings: list[dict[str, Any]] = []
    existing_allowed, allowed_findings = _normalize_rule_list(canonical.get("allowed"), "sideEffects.allowed")
    existing_forbidden, forbidden_findings = _normalize_rule_list(canonical.get("forbidden"), "sideEffects.forbidden")
    findings.extend(allowed_findings)
    findings.extend(forbidden_findings)
    if "allowed" in canonical:
        canonical["allowed"] = existing_allowed
    if "forbidden" in canonical:
        canonical["forbidden"] = existing_forbidden
    legacy_rules = policy.get("rules")
    if not isinstance(legacy_rules, list) or not legacy_rules:
        _ensure_canonical_lists(canonical)
        return canonical, findings

    migrated_allowed: list[dict[str, Any]] = []
    migrated_forbidden: list[dict[str, Any]] = []
    ambiguous = False
    for index, item in enumerate(legacy_rules):
        migrated, target = _migrate_legacy_rule(item)
        if migrated is None or target is None:
            ambiguous = True
            findings.append(
                PolicyCompatibilityFinding(
                    code="legacy-side-effect-rule-ambiguous",
                    severity="blocking",
                    path=f"sideEffects.rules[{index}]",
                    message="Legacy side-effect rule cannot be migrated safely because its effect or match envelope is ambiguous.",
                    migrationAvailable=False,
                    guidedChoices=_policy_guided_choices(),
                    blocksExecution=True,
                ).to_dict()
            )
            continue
        if target == "allowed":
            migrated_allowed.append(migrated)
        else:
            migrated_forbidden.append(migrated)

    existing_allowed = list(canonical.get("allowed", [])) if isinstance(canonical.get("allowed"), list) else []
    existing_forbidden = list(canonical.get("forbidden", [])) if isinstance(canonical.get("forbidden"), list) else []
    if ambiguous:
        _ensure_canonical_lists(canonical)
        return canonical, findings

    conflict = False
    if existing_allowed and migrated_allowed and not _same_rules(existing_allowed, migrated_allowed):
        conflict = True
    if existing_forbidden and migrated_forbidden and not _same_rules(existing_forbidden, migrated_forbidden):
        conflict = True
    if conflict:
        findings.append(
            PolicyCompatibilityFinding(
                code="conflicting-side-effect-policy",
                severity="blocking",
                path="sideEffects",
                message="Legacy side-effect policy conflicts with canonical allowed/forbidden policy. Choose which policy represents owner intent before running.",
                migrationAvailable=False,
                guidedChoices=_policy_guided_choices(),
                blocksExecution=True,
            ).to_dict()
        )
        _ensure_canonical_lists(canonical)
        return canonical, findings

    if migrated_allowed and not existing_allowed:
        canonical["allowed"] = migrated_allowed
    if migrated_forbidden and not existing_forbidden:
        canonical["forbidden"] = migrated_forbidden
    findings.append(
        PolicyCompatibilityFinding(
            code="legacy-side-effect-rules",
            severity="warning",
            path="sideEffects.rules",
            message="Legacy side-effect rules were migrated to Core-compatible allowed/forbidden policy fields.",
            migrationAvailable=True,
            guidedChoices=[],
            blocksExecution=False,
        ).to_dict()
    )
    _ensure_canonical_lists(canonical)
    return canonical, findings


def policy_compatibility_findings(policy: dict[str, Any] | None) -> list[dict[str, Any]]:
    _canonical, findings = normalize_side_effect_policy(policy)
    return findings


def effective_confirmation_support(
    signal_type: str,
    *,
    core_contract: dict[str, Any] | None = None,
    runtime_outcomes: list[dict[str, Any] | None] | None = None,
) -> ConfirmationSignalSupport:
    static_types = set(_confirmation_signal_types(core_contract))
    static_support = signal_type in static_types if static_types else signal_type in {"finalUrl", "runtimeOutput", "allowedNetworkObservation"}
    explicit_runtime = _explicit_runtime_confirmation_support(core_contract, signal_type)
    unsupported_evidence = _runtime_unsupported_confirmation_evidence(runtime_outcomes or [], signal_type)
    if explicit_runtime is not None:
        runtime_support = explicit_runtime
        evidence = "public runtime capability data proves support" if explicit_runtime else "public runtime capability data marks unsupported"
    elif unsupported_evidence:
        runtime_support = False
        evidence = unsupported_evidence
    else:
        runtime_support = None
        evidence = "static public contract projection"
    return ConfirmationSignalSupport(
        signalType=signal_type,
        staticSupport=static_support,
        runtimeSupport=runtime_support,
        effectiveSupport=bool(static_support and runtime_support is not False),
        evidence=evidence,
    )


def confirmation_support_findings(
    signals: list[dict[str, Any]],
    *,
    core_contract: dict[str, Any] | None = None,
    runtime_outcomes: list[dict[str, Any] | None] | None = None,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for index, signal in enumerate(signals):
        signal_type = str(signal.get("type") or signal.get("source") or "")
        if not signal_type:
            continue
        support = effective_confirmation_support(signal_type, core_contract=core_contract, runtime_outcomes=runtime_outcomes)
        if support.effectiveSupport:
            continue
        findings.append(
            {
                "severity": "blocking",
                "code": "unsupported-confirmation-signal",
                "path": f"sideEffects.confirmationSignals[{index}].type",
                "message": (
                    f"Confirmation signal type '{signal_type}' is not proven runtime-supported; "
                    f"runtime outcome or capability evidence: {support.evidence}."
                ),
                "signalType": signal_type,
                "support": support.to_dict(),
            }
        )
    return findings


def evaluate_rerun_decision(record: Any, *, supersede_reviews: list[Any] | None = None) -> dict[str, Any]:
    side_effect = record.sideEffects if isinstance(record.sideEffects, dict) else {}
    if side_effect.get("class") not in {"write", "external-notification"}:
        return {"decision": "allowed", "reason": "No write rerun guard is required for this side-effect class.", "refreshRuntimeInputs": []}
    last_run = record.lastRun if isinstance(record.lastRun, dict) else None
    if not last_run:
        return {"decision": "allowed", "reason": "No previous run recorded for this write use case.", "refreshRuntimeInputs": []}
    interpretation = last_run.get("postCommitInterpretation") if isinstance(last_run.get("postCommitInterpretation"), dict) else {}
    classification = last_run.get("resultClassification") if isinstance(last_run.get("resultClassification"), dict) else {}
    core_risk = str(interpretation.get("rerunRisk") or classification.get("rerunRisk") or "")
    supersede = _matching_supersede_review(last_run, supersede_reviews or [])
    if supersede is not None:
        resulting = getattr(supersede, "resultingClassification", None)
        if not isinstance(resulting, dict) and isinstance(supersede, dict):
            resulting = supersede.get("resultingClassification")
        if isinstance(resulting, dict) and resulting.get("rerunRisk"):
            core_risk = str(resulting["rerunRisk"])
    side_effect_may_exist = bool(interpretation.get("sideEffectMayExist"))
    if not core_risk:
        core_risk = "requires-confirmation" if side_effect_may_exist else "safe"
    policy = RerunPolicy.from_dict(record.rerunPolicy)
    spec_decision = policy.afterCommit if side_effect_may_exist or interpretation.get("postCommit") else policy.afterNoCommit
    decision = combine_rerun_decision(core_risk, spec_decision)
    refreshable = {item.name for item in record.runtimeInputs if item.source == "generated" and item.refreshOnRerunAfterCommit}
    refresh_names = [name for name in policy.refreshRuntimeInputs if name in refreshable]
    if decision == "allowed-with-new-inputs" and not refresh_names:
        return {
            "decision": "blocked",
            "coreRisk": core_risk,
            "specDecision": spec_decision,
            "reason": "Rerun requires refreshed generated inputs, but no declared refreshable generated input is available.",
            "refreshRuntimeInputs": [],
            "nextAction": f"Update rerunPolicy.refreshRuntimeInputs for {record.alias} before rerunning.",
        }
    if decision == "blocked":
        reason = "Rerun is blocked by the previous write outcome and declared rerun policy."
        next_action = "Review or supersede the previous write outcome before rerunning."
    elif decision == "requires-confirmation":
        reason = "Rerun requires explicit owner confirmation because the previous write may have crossed the commit boundary."
        next_action = "Confirm the write rerun risk or review the previous outcome before running."
    elif decision == "allowed-with-new-inputs":
        reason = "Rerun is allowed only with refreshed generated runtime inputs."
        next_action = "Proceed with run."
    else:
        reason = "Rerun is allowed by Core risk and Spec rerun policy."
        next_action = "Proceed with run."
    return {
        "decision": decision,
        "coreRisk": core_risk,
        "specDecision": spec_decision,
        "reason": reason,
        "refreshRuntimeInputs": refresh_names,
        "nextAction": next_action,
        **({"supersededBy": getattr(supersede, "reviewId", None) or (supersede.get("reviewId") if isinstance(supersede, dict) else None)} if supersede is not None else {}),
    }


def _migrate_legacy_rule(item: Any) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(item, dict):
        return None, None
    effect = str(item.get("effect") or "").lower()
    if effect in {"allow", "allowed"}:
        target = "allowed"
    elif effect in {"forbid", "forbidden", "deny", "block"}:
        target = "forbidden"
    else:
        return None, None
    match = item.get("match") if isinstance(item.get("match"), dict) else {}
    if not match:
        return None, None
    migrated_input: dict[str, Any] = {}
    if item.get("id"):
        migrated_input["id"] = str(item["id"])
    for key, value in match.items():
        if value is not None:
            migrated_input[str(key)] = value
    migrated, rule_findings = _normalize_rule(migrated_input, "sideEffects.rules[]")
    if rule_findings:
        return None, None
    return migrated, target


def _ensure_canonical_lists(policy: dict[str, Any]) -> None:
    if "allowed" in policy and not isinstance(policy.get("allowed"), list):
        policy["allowed"] = []
    if "forbidden" in policy and not isinstance(policy.get("forbidden"), list):
        policy["forbidden"] = []


def _normalize_rule_list(value: Any, path: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not isinstance(value, list):
        return [], []
    normalized: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        rule, rule_findings = _normalize_rule(item, f"{path}[{index}]")
        findings.extend(rule_findings)
        normalized.append(rule if rule is not None else dict(item) if isinstance(item, dict) else {})
    return normalized, findings


def _normalize_rule(item: Any, path: str) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    if not isinstance(item, dict):
        return None, [
            PolicyCompatibilityFinding(
                code="side-effect-rule-invalid",
                severity="blocking",
                path=path,
                message="Side-effect rule must be an object in the Core-compatible allowed/forbidden rule shape.",
                migrationAvailable=False,
                guidedChoices=_policy_guided_choices(),
                blocksExecution=True,
            ).to_dict()
        ]
    if not item.get("id"):
        return None, [
            PolicyCompatibilityFinding(
                code="side-effect-rule-missing-id",
                severity="blocking",
                path=f"{path}.id",
                message="Side-effect rule requires an explicit id; Spec will not generate write-safety rule identities automatically.",
                migrationAvailable=False,
                guidedChoices=_policy_guided_choices(),
                blocksExecution=True,
            ).to_dict()
        ]
    if not item.get("urlContains") and not item.get("urlPattern"):
        return None, [
            PolicyCompatibilityFinding(
                code="side-effect-rule-missing-url-match",
                severity="blocking",
                path=f"{path}.urlContains",
                message="Side-effect rule requires urlContains or urlPattern so Core can match the observed request.",
                migrationAvailable=False,
                guidedChoices=_policy_guided_choices(),
                blocksExecution=True,
            ).to_dict()
        ]

    normalized: dict[str, Any] = {"id": str(item["id"])}
    normalized["kind"] = str(item.get("kind") or "network")
    normalized["methods"] = _normalize_methods(item)
    for key, value in item.items():
        if key in {"id", "kind", "method", "methods"}:
            continue
        if value is not None:
            normalized[str(key)] = value
    return normalized, []


def _normalize_methods(item: dict[str, Any]) -> list[str]:
    raw_methods = item.get("methods")
    if isinstance(raw_methods, list):
        return [str(method).upper() for method in raw_methods if str(method or "").strip()]
    method = item.get("method")
    if method is None:
        return []
    value = str(method).strip()
    return [value.upper()] if value else []


def _same_rules(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> bool:
    return _normalized_rules(left) == _normalized_rules(right)


def _normalized_rules(rules: list[dict[str, Any]]) -> list[str]:
    return sorted(json.dumps(item, sort_keys=True, separators=(",", ":")) for item in rules)


def _policy_guided_choices() -> list[dict[str, str]]:
    return [
        {"id": "keep-canonical", "label": "Keep canonical policy", "description": "Use allowed/forbidden as already authored and discard legacy rules."},
        {"id": "migrate-legacy", "label": "Migrate legacy rules", "description": "Replace canonical entries with the migrated legacy rule intent."},
        {"id": "ask-owner", "label": "Ask owner", "description": "Pause for an explicit owner decision before readiness or run."},
    ]


def confirmation_support_to_dict(support: ConfirmationSignalSupport) -> dict[str, Any]:
    return {key: value for key, value in asdict(support).items() if value is not None}


def _confirmation_signal_types(core_contract: dict[str, Any] | None) -> list[str]:
    guardrails = _side_effect_guardrails(core_contract)
    values = guardrails.get("confirmationSignalTypes")
    return [str(item) for item in values] if isinstance(values, list) else []


def _explicit_runtime_confirmation_support(core_contract: dict[str, Any] | None, signal_type: str) -> bool | None:
    guardrails = _side_effect_guardrails(core_contract)
    candidates = guardrails.get("runtimeConfirmationSupport") or guardrails.get("confirmationRuntimeSupport")
    if isinstance(candidates, dict):
        raw = candidates.get(signal_type)
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, str):
            return raw.lower() == "supported"
    if isinstance(candidates, list):
        for item in candidates:
            if not isinstance(item, dict):
                continue
            if str(item.get("type") or item.get("signalType") or "") != signal_type:
                continue
            status = item.get("status")
            if isinstance(status, bool):
                return status
            if isinstance(status, str):
                return status.lower() in {"supported", "stable", "ready"}
    return None


def _runtime_unsupported_confirmation_evidence(outcomes: list[dict[str, Any] | None], signal_type: str) -> str:
    for outcome in outcomes:
        for item in _iter_dicts(outcome):
            code = str(item.get("code") or item.get("reason") or "")
            status = str(item.get("status") or "").lower()
            observed_type = str(item.get("type") or item.get("signalType") or item.get("source") or "")
            if observed_type and observed_type != signal_type:
                continue
            if code == "unsupported-confirmation-signal" or status == "unsupported":
                return f"runtime outcome reported unsupported-confirmation-signal for {signal_type}"
    return ""


def _iter_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _iter_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_dicts(child)


def _side_effect_guardrails(core_contract: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(core_contract, dict):
        return {}
    sections = core_contract.get("sections") if isinstance(core_contract.get("sections"), dict) else {}
    guardrails = sections.get("sideEffectGuardrails") if isinstance(sections.get("sideEffectGuardrails"), dict) else {}
    return guardrails if isinstance(guardrails, dict) else {}


def _matching_supersede_review(last_run: dict[str, Any], reviews: list[Any]) -> Any | None:
    run_id = str(last_run.get("runId") or "")
    if not run_id:
        return None
    for review in reviews:
        source_run_id = getattr(review, "sourceRunId", None)
        if source_run_id is None and isinstance(review, dict):
            source_run_id = review.get("sourceRunId")
        if str(source_run_id or "") == run_id:
            return review
    return None
