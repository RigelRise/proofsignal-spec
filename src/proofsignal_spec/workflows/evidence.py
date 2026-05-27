from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .browser_authoring import VALID_NETWORK_MATCH_KEYS
from .models import BackendRequestCheck, EvidenceInventory, PlannedValidationGate, RenderedResultAssertion, RuntimeEvidence, ScreenshotEvidence

GENERIC_BODY_TARGETS = {"body", "page", "pagebody", "pageBody", "document", "root"}


def slugify_gate_id(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "gate"


def normalize_planned_gates(items: list[Any]) -> tuple[list[PlannedValidationGate], list[str]]:
    gates: list[PlannedValidationGate] = []
    warnings: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(items, start=1):
        if isinstance(item, dict):
            gate = PlannedValidationGate.from_dict(item)
            if not gate.id:
                gate.id = slugify_gate_id(gate.description or f"gate-{index}")
            if gate.condition and gate.conditionEvaluation is None:
                gate.conditionEvaluation = "not-evaluated"
        else:
            text = str(item)
            gate = PlannedValidationGate(
                id=slugify_gate_id(text),
                description=text,
                required=True,
                legacy=True,
            )
            warnings.append(
                f"Legacy string validation gate '{text}' was normalized to gateId '{gate.id}'. Replan to make gate coverage explicit."
            )
        original = gate.id
        suffix = 2
        while gate.id in seen:
            gate.id = f"{original}-{suffix}"
            suffix += 1
        seen.add(gate.id)
        gates.append(gate)
    return gates, warnings


def extract_browser_evidence(
    browser: dict[str, Any],
    *,
    source_artifact: str | None = None,
    known_gate_ids: set[str] | None = None,
) -> EvidenceInventory:
    inventory = EvidenceInventory()
    targets = browser.get("targets") if isinstance(browser.get("targets"), dict) else {}
    known_gate_ids = known_gate_ids or set()

    for step in _list(browser.get("steps")):
        if not isinstance(step, dict):
            continue
        gate_id = _gate_id(step)
        action = step.get("action")
        evidence_id = _evidence_id(step, action or "step")
        if not gate_id:
            if action in {"waitForText", "checkText", "awaitNetwork", "captureScreenshot"}:
                inventory.unmappedEvidence.append({"id": evidence_id, "kind": str(action), "sourceArtifact": source_artifact})
            continue
        if known_gate_ids and gate_id not in known_gate_ids:
            inventory.blockers.append(f"Evidence {evidence_id} references unknown gateId '{gate_id}'.")
            continue
        if action in {"waitForText", "checkText"}:
            target = str(step.get("target") or "")
            inventory.uiAssertions.append(
                RenderedResultAssertion(
                    id=evidence_id,
                    gateId=gate_id,
                    target=target,
                    kind="text",
                    expected=step.get("value"),
                    domainSemantics=_domain_semantics(targets, target),
                    sourceArtifact=source_artifact,
                )
            )
            if _is_generic_target(target, targets):
                inventory.warnings.append(
                    f"Evidence {evidence_id} uses generic target '{target}' and may not prove a domain-specific rendered result."
                )
        elif action == "awaitNetwork":
            check, blockers = _network_check_from_step(step, evidence_id, gate_id, source_artifact)
            inventory.networkChecks.append(check)
            inventory.blockers.extend(blockers)
        elif action == "captureScreenshot":
            inventory.screenshots.append(
                ScreenshotEvidence(
                    id=evidence_id,
                    gateId=gate_id,
                    name=str(step.get("value")) if step.get("value") is not None else None,
                    sourceArtifact=source_artifact,
                )
            )

    for assertion in _list(browser.get("assertions")):
        if not isinstance(assertion, dict):
            continue
        gate_id = _gate_id(assertion)
        kind = str(assertion.get("kind") or "")
        evidence_id = _evidence_id(assertion, kind or "assertion")
        if not gate_id:
            if kind in {"text", "visible", "hidden", "screenshot-required"}:
                inventory.unmappedEvidence.append({"id": evidence_id, "kind": kind, "sourceArtifact": source_artifact})
            continue
        if known_gate_ids and gate_id not in known_gate_ids:
            inventory.blockers.append(f"Evidence {evidence_id} references unknown gateId '{gate_id}'.")
            continue
        if kind == "screenshot-required":
            inventory.screenshots.append(
                ScreenshotEvidence(id=evidence_id, gateId=gate_id, name=str(assertion.get("expected") or evidence_id), sourceArtifact=source_artifact)
            )
            continue
        if kind in {"text", "visible", "hidden"}:
            target = str(assertion.get("target") or "")
            inventory.uiAssertions.append(
                RenderedResultAssertion(
                    id=evidence_id,
                    gateId=gate_id,
                    target=target,
                    kind=kind,
                    expected=assertion.get("expected"),
                    domainSemantics=_domain_semantics(targets, target) or assertion.get("domainSemantics"),
                    sourceArtifact=source_artifact,
                )
            )
            if _is_generic_target(target, targets):
                inventory.warnings.append(
                    f"Evidence {evidence_id} uses generic target '{target}' and may not prove a domain-specific rendered result."
                )
    return inventory


def merge_evidence(inventories: list[EvidenceInventory]) -> EvidenceInventory:
    merged = EvidenceInventory()
    for inventory in inventories:
        merged.uiAssertions.extend(inventory.uiAssertions)
        merged.networkChecks.extend(inventory.networkChecks)
        merged.screenshots.extend(inventory.screenshots)
        merged.unmappedEvidence.extend(inventory.unmappedEvidence)
        merged.blockers.extend(inventory.blockers)
        merged.warnings.extend(inventory.warnings)
    return merged


def extract_core_runtime_evidence(
    result: dict[str, Any],
    *,
    known_gate_ids: set[str] | None = None,
) -> EvidenceInventory:
    """Normalize public Core run evidence into the Spec evidence inventory.

    The adapter only consumes documented/public JSON fields. Current Core
    versions may omit this section entirely; callers should treat that as
    missing runtime evidence rather than inspect private report internals.
    """

    inventory = EvidenceInventory()
    known_gate_ids = known_gate_ids or set()
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    items = data.get("gateEvidence") or data.get("evidence") or []
    if not isinstance(items, list):
        return inventory

    for index, raw in enumerate(items, start=1):
        if not isinstance(raw, dict):
            continue
        evidence = _runtime_evidence_from_dict(raw, index)
        if evidence.gateId and known_gate_ids and evidence.gateId not in known_gate_ids:
            inventory.blockers.append(f"Runtime evidence {evidence.evidenceId} references unknown gateId '{evidence.gateId}'.")
            continue
        if not evidence.gateId:
            inventory.unmappedEvidence.append(evidence.to_dict())
            continue
        if evidence.source == "network":
            inventory.networkChecks.append(
                BackendRequestCheck(
                    id=evidence.evidenceId,
                    gateId=evidence.gateId,
                    method=str(raw.get("method")) if raw.get("method") is not None else None,
                    urlContains=str(raw.get("urlContains")) if raw.get("urlContains") is not None else None,
                    operationName=str(raw.get("operationName")) if raw.get("operationName") is not None else None,
                    expectedStatus=raw.get("expectedStatus") or raw.get("statusCode"),
                    publicMatchKeys=[str(item) for item in raw.get("publicMatchKeys", []) if item],
                    sensitiveFieldsExcluded=True,
                    sourceArtifact=evidence.artifactRef,
                )
            )
        elif evidence.source == "screenshot":
            inventory.screenshots.append(
                ScreenshotEvidence(
                    id=evidence.evidenceId,
                    gateId=evidence.gateId,
                    name=str(raw.get("name") or raw.get("artifactRef") or evidence.evidenceId),
                    sourceArtifact=evidence.artifactRef,
                )
            )
        else:
            inventory.uiAssertions.append(
                RenderedResultAssertion(
                    id=evidence.evidenceId,
                    gateId=evidence.gateId,
                    target=str(raw.get("target") or raw.get("selector") or evidence.evidenceId),
                    kind=str(raw.get("kind") or evidence.source),
                    expected=raw.get("expected"),
                    domainSemantics=str(raw.get("domainSemantics")) if raw.get("domainSemantics") else None,
                    sourceArtifact=evidence.artifactRef,
                )
            )
    return inventory


def browser_from_skill_content(content: str) -> dict[str, Any]:
    data = _load_skill_yaml(content)
    browser = data.get("browser") if isinstance(data, dict) else None
    return browser if isinstance(browser, dict) else {}


def _runtime_evidence_from_dict(raw: dict[str, Any], index: int) -> RuntimeEvidence:
    source = str(raw.get("source") or raw.get("type") or raw.get("kind") or "assertion")
    normalized_source = _runtime_source(source)
    specificity = str(raw.get("specificity") or ("rendered-result" if normalized_source in {"step", "assertion"} else "supporting"))
    if specificity not in {"rendered-result", "supporting", "generic"}:
        specificity = "supporting"
    status = str(raw.get("status") or "unknown")
    if status not in {"passed", "failed", "skipped", "unknown"}:
        status = "unknown"
    return RuntimeEvidence(
        evidenceId=str(raw.get("evidenceId") or raw.get("id") or f"runtime-evidence-{index}"),
        source=normalized_source,
        gateId=str(raw.get("gateId") or raw.get("gate") or "").strip() or None,
        status=status,  # type: ignore[arg-type]
        specificity=specificity,  # type: ignore[arg-type]
        artifactRef=str(raw.get("artifactRef") or raw.get("sourceArtifact") or "").strip() or None,
        redactionStatus="not-sensitive",
    )


def _runtime_source(value: str) -> str:
    lowered = value.lower()
    if "network" in lowered or "request" in lowered:
        return "network"
    if "screenshot" in lowered:
        return "screenshot"
    if "step" in lowered:
        return "step"
    if "profile" in lowered:
        return "profile-setting"
    if "report" in lowered:
        return "report-summary"
    return "assertion"


def browser_from_skill_path(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return browser_from_skill_content(path.read_text(encoding="utf-8"))


def _load_skill_yaml(content: str) -> dict[str, Any]:
    text = content.strip()
    if "```" in text:
        match = re.search(r"```(?:yaml|yml)?\s*(.*?)```", text, flags=re.S | re.I)
        if match:
            text = match.group(1).strip()
    elif text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[1].strip()
    try:
        import yaml  # type: ignore

        parsed = yaml.safe_load(text) or {}
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _network_check_from_step(
    step: dict[str, Any],
    evidence_id: str,
    gate_id: str,
    source_artifact: str | None,
) -> tuple[BackendRequestCheck, list[str]]:
    match = step.get("match") if isinstance(step.get("match"), dict) else {}
    method = match.get("method") or step.get("method")
    expected_status = match.get("status") or match.get("expectedStatus") or step.get("expectedStatus")
    public_keys = sorted(str(key) for key in match if key in VALID_NETWORK_MATCH_KEYS and match.get(key) is not None)
    check = BackendRequestCheck(
        id=evidence_id,
        gateId=gate_id,
        method=str(method) if method is not None else None,
        urlContains=str(match.get("urlContains")) if match.get("urlContains") is not None else None,
        operationName=str(match.get("operationName") or step.get("operationName")) if match.get("operationName") or step.get("operationName") else None,
        expectedStatus=expected_status,
        publicMatchKeys=public_keys,
        sensitiveFieldsExcluded=True,
        sourceArtifact=source_artifact,
    )
    blockers: list[str] = []
    if not method:
        blockers.append(f"Network evidence {evidence_id} must declare method.")
    if not expected_status:
        blockers.append(f"Network evidence {evidence_id} must declare expected status.")
    if not any(key in public_keys for key in {"urlContains", "requestBodyContains", "responseBodyContains"}):
        blockers.append(f"Network evidence {evidence_id} must declare a supported public match pattern beyond operationName.")
    return check, blockers


def _gate_id(item: dict[str, Any]) -> str | None:
    value = item.get("gateId") or item.get("gate")
    return str(value).strip() if value else None


def _evidence_id(item: dict[str, Any], prefix: str) -> str:
    return str(item.get("id") or f"{prefix}-evidence")


def _domain_semantics(targets: dict[str, Any], target: str) -> str | None:
    bundle = targets.get(target)
    if isinstance(bundle, dict) and bundle.get("domainSemantics"):
        return str(bundle["domainSemantics"])
    return None


def _is_generic_target(target: str, targets: dict[str, Any]) -> bool:
    if target in GENERIC_BODY_TARGETS or target.lower() in {item.lower() for item in GENERIC_BODY_TARGETS}:
        return True
    bundle = targets.get(target)
    if isinstance(bundle, dict):
        css = str(bundle.get("css") or "").strip().lower()
        semantics = str(bundle.get("domainSemantics") or "").lower()
        return css in {"body", "html", "*"} and "empty state" not in semantics and "page-level" not in semantics
    return False


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
