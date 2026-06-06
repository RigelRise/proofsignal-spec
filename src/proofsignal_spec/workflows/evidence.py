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
    core_contract: dict[str, Any] | None = None,
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
            check, blockers = _network_check_from_step(step, evidence_id, gate_id, source_artifact, core_contract=core_contract)
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
    core_contract: dict[str, Any] | None = None,
) -> EvidenceInventory:
    """Normalize public Core run evidence into the Spec evidence inventory.

    The adapter only consumes documented/public JSON fields. Core may expose
    normalized gate evidence on the run envelope, or a public qa-report/v1
    payload with step/precondition gateIds.
    """

    known_gate_ids = known_gate_ids or set()
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    report = data.get("report") if isinstance(data.get("report"), dict) else None
    if report is None and isinstance(result.get("report"), dict):
        report = result.get("report")

    report_rules = _report_coverage_rules(core_contract)
    report_inventory = _extract_qa_report_runtime_evidence(
        report,
        known_gate_ids=known_gate_ids,
        source_artifact=str(data.get("reportPath") or "").strip() or None,
        report_rules=report_rules,
    )
    if _qa_report_has_gate_items(report, report_rules=report_rules):
        return report_inventory

    items = data.get("gateEvidence") or data.get("evidence") or []
    return _extract_runtime_evidence_items(items, known_gate_ids=known_gate_ids)


def _extract_runtime_evidence_items(items: Any, *, known_gate_ids: set[str]) -> EvidenceInventory:
    inventory = EvidenceInventory()
    if not isinstance(items, list):
        return inventory
    for index, raw in enumerate(items, start=1):
        if not isinstance(raw, dict):
            continue
        _append_runtime_evidence(inventory, raw, index=index, known_gate_ids=known_gate_ids)
    return inventory


def _extract_qa_report_runtime_evidence(
    report: dict[str, Any] | None,
    *,
    known_gate_ids: set[str],
    source_artifact: str | None,
    report_rules: dict[str, Any],
) -> EvidenceInventory:
    inventory = EvidenceInventory()
    if not isinstance(report, dict) or report.get("schemaVersion") != report_rules["schemaVersion"]:
        return inventory
    tolerated_ids = _tolerated_failure_ids(report.get("toleratedFailures"))
    index = 1
    for section in report_rules["stepCollections"]:
        items = report.get(section)
        if not isinstance(items, list):
            continue
        for raw in items:
            if not isinstance(raw, dict):
                continue
            if _is_tolerated_failure(raw, tolerated_ids):
                continue
            _append_passed_report_item(
                inventory,
                raw,
                index=index,
                known_gate_ids=known_gate_ids,
                source_artifact=source_artifact,
                report_rules=report_rules,
            )
            index += 1
    return inventory


def _append_passed_report_item(
    inventory: EvidenceInventory,
    raw: dict[str, Any],
    *,
    index: int,
    known_gate_ids: set[str],
    source_artifact: str | None,
    report_rules: dict[str, Any],
) -> None:
    if str(raw.get("status") or "").lower() != "passed":
        return
    item = _normalize_report_gate_id(raw, report_rules)
    item.setdefault("source", "step")
    item.setdefault("artifactRef", source_artifact)
    _append_runtime_evidence(inventory, item, index=index, known_gate_ids=known_gate_ids)
    offset = 1
    for collection in report_rules["evidenceCollections"]:
        evidence_items = raw.get(collection)
        if not isinstance(evidence_items, list):
            continue
        for child in evidence_items:
            if not isinstance(child, dict):
                continue
            if _is_tolerated_failure(child, set()):
                continue
            child_item = _normalize_report_gate_id(child, report_rules)
            child_item.setdefault("gateId", item.get("gateId"))
            child_item.setdefault("status", raw.get("status"))
            child_item.setdefault("artifactRef", source_artifact)
            if not any(child_item.get(key) for key in ("source", "type", "kind")):
                child_item["source"] = _evidence_source_from_child(child_item)
            _append_runtime_evidence(inventory, child_item, index=(index * 1000) + offset, known_gate_ids=known_gate_ids)
            offset += 1


def _append_runtime_evidence(
    inventory: EvidenceInventory,
    raw: dict[str, Any],
    *,
    index: int,
    known_gate_ids: set[str],
) -> None:
    evidence = _runtime_evidence_from_dict(raw, index)
    if evidence.gateId and known_gate_ids and evidence.gateId not in known_gate_ids:
        inventory.blockers.append(f"Runtime evidence {evidence.evidenceId} references unknown gateId '{evidence.gateId}'.")
        return
    if not evidence.gateId:
        inventory.unmappedEvidence.append(evidence.to_dict())
        return
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


def _qa_report_has_gate_items(report: dict[str, Any] | None, *, report_rules: dict[str, Any]) -> bool:
    if not isinstance(report, dict) or report.get("schemaVersion") != report_rules["schemaVersion"]:
        return False
    for section in report_rules["stepCollections"]:
        items = report.get(section)
        if not isinstance(items, list):
            continue
        for raw in items:
            if not isinstance(raw, dict):
                continue
            if _gate_id(raw, report_rules=report_rules):
                return True
            for collection in report_rules["evidenceCollections"]:
                evidence_items = raw.get(collection)
                if isinstance(evidence_items, list) and any(isinstance(child, dict) and _gate_id(child, report_rules=report_rules) for child in evidence_items):
                    return True
    return False


def _tolerated_failure_ids(raw: Any) -> set[str]:
    if not isinstance(raw, list):
        return set()
    ids: set[str] = set()
    for item in raw:
        if isinstance(item, dict):
            value = item.get("stepId") or item.get("id")
        else:
            value = item
        if value:
            ids.add(str(value))
    return ids


def _is_tolerated_failure(item: dict[str, Any], tolerated_ids: set[str]) -> bool:
    if item.get("toleratedFailure") is True:
        return True
    if str(item.get("toleratedFailure") or "").lower() in {"true", "1", "yes"}:
        return True
    item_id = item.get("id")
    return bool(item_id and str(item_id) in tolerated_ids)


def _evidence_source_from_child(item: dict[str, Any]) -> str:
    values = " ".join(str(item.get(key) or "") for key in ("id", "name", "artifactRef", "path", "file"))
    return "screenshot" if "screenshot" in values.lower() else "assertion"


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


def _report_coverage_rules(core_contract: dict[str, Any] | None) -> dict[str, Any]:
    section = {}
    if isinstance(core_contract, dict):
        raw_section = core_contract.get("sections", {}).get("reportCoverage", {})
        if isinstance(raw_section, dict):
            section = raw_section
    return {
        "schemaVersion": str(section.get("schemaVersion") or "qa-report/v1"),
        "gateIdFields": [str(item) for item in section.get("gateIdFields", ["gateId"]) if item],
        "stepCollections": [str(item) for item in section.get("stepCollections", ["steps", "preconditions"]) if item],
        "evidenceCollections": [str(item) for item in section.get("evidenceCollections", ["evidence"]) if item],
    }


def _normalize_report_gate_id(raw: dict[str, Any], report_rules: dict[str, Any]) -> dict[str, Any]:
    item = dict(raw)
    if item.get("gateId"):
        return item
    for field in report_rules["gateIdFields"]:
        if item.get(field):
            item["gateId"] = item[field]
            return item
    return item


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
    *,
    core_contract: dict[str, Any] | None = None,
) -> tuple[BackendRequestCheck, list[str]]:
    match = step.get("match") if isinstance(step.get("match"), dict) else {}
    network_keys = _network_match_keys_from_contract(core_contract)
    method = match.get("method") or step.get("method")
    expected_status = match.get("status") or match.get("expectedStatus") or step.get("expectedStatus")
    public_keys = sorted(str(key) for key in match if key in network_keys and match.get(key) is not None)
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
    public_pattern_keys = [key for key in public_keys if key not in {"method", "status", "expectedStatus", "operationName"}]
    if not public_pattern_keys:
        blockers.append(f"Network evidence {evidence_id} must declare a supported public match pattern beyond operationName.")
    return check, blockers


def _network_match_keys_from_contract(core_contract: dict[str, Any] | None) -> set[str]:
    if isinstance(core_contract, dict):
        browser = core_contract.get("sections", {}).get("browserWorkflow", {})
        if isinstance(browser, dict) and isinstance(browser.get("validNetworkMatchKeys"), list):
            keys = {str(item) for item in browser["validNetworkMatchKeys"] if item}
            if keys:
                return keys
    return set(VALID_NETWORK_MATCH_KEYS)


def _gate_id(item: dict[str, Any], *, report_rules: dict[str, Any] | None = None) -> str | None:
    values = [item.get("gateId"), item.get("gate")]
    if report_rules:
        values.extend(item.get(field) for field in report_rules["gateIdFields"])
    value = next((candidate for candidate in values if candidate), None)
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
