from __future__ import annotations

from typing import Any

VALID_BROWSER_ACTIONS = {
    "navigate",
    "click",
    "fill",
    "select",
    "waitForText",
    "checkText",
    "checkLocation",
    "captureScreenshot",
    "scrollIntoView",
    "awaitNetwork",
    "repeatUntil",
}

VALID_ASSERTION_KINDS = {"text", "location", "visible", "hidden", "screenshot-required"}
VALID_NETWORK_MATCH_KEYS = {"urlContains", "method", "status", "requestBodyContains", "responseBodyContains"}
TARGET_SIGNAL_KEYS = ("testId", "label", "text", "css", "semanticLocator", "all")

ACTION_REQUIREMENTS = {
    "navigate": {"required": ["value"], "notes": "The URL goes in value, not target."},
    "click": {"required": ["target"], "notes": "target must name a browser.targets entry."},
    "fill": {"required": ["target", "value"], "notes": "target must name a browser.targets entry; value must be a string."},
    "select": {"required": ["target", "value"], "notes": "target must name a browser.targets entry; value must be a string."},
    "waitForText": {"required": ["target", "value"], "notes": "Use a named target plus the text to wait for."},
    "checkText": {"required": ["target", "value"], "notes": "Use a named target plus the expected visible text."},
    "checkLocation": {"required": ["value"], "notes": "value is the URL fragment or location expectation."},
    "captureScreenshot": {"required": [], "notes": "value may name the evidence screenshot."},
    "scrollIntoView": {"required": ["target"], "notes": "target must name a browser.targets entry."},
    "awaitNetwork": {"required": ["match"], "notes": "match must include at least one supported network field."},
    "repeatUntil": {"required": ["until", "do"], "notes": "Use supported condition/action blocks."},
}


def browser_authoring_contract() -> dict[str, Any]:
    return {
        "schemaVersion": "proofsignal-browser-authoring-contract/v1",
        "validActions": sorted(VALID_BROWSER_ACTIONS),
        "validAssertionKinds": sorted(VALID_ASSERTION_KINDS),
        "validNetworkMatchKeys": sorted(VALID_NETWORK_MATCH_KEYS),
        "targetRules": {
            "stepsReferenceNamedTargets": "Step target values must be aliases declared under browser.targets, not inline CSS, text=, placeholder=, xpath, or role selectors.",
            "targetSignalPriority": ["testId", "label", "text", "css", "semanticLocator"],
            "singlePrimarySignal": "Declare one primary selector signal per target. If a target has both label and css, Core uses label first and ignores css.",
            "composition": "Use all only when multiple signals must match the same element. all entries support testId or css.",
        },
        "actionRequirements": ACTION_REQUIREMENTS,
        "assertionRules": {
            "text": "Requires target and expected. Assertions run after all steps complete.",
            "location": "Requires expected.",
            "visible": "Requires target.",
            "hidden": "Requires target.",
            "screenshot-required": "Use for intermediate visual gates captured during steps.",
            "fieldName": "Assertions use expected, not value.",
        },
        "timingGuidance": [
            "For debounced inputs, do not rely on awaitNetwork immediately after fill; the request may not have fired yet.",
            "Prefer checkText or waitForText with a longer timeout to wait through debounce, API response, and render.",
        ],
        "examples": {
            "target": {"searchInput": {"css": "input#search", "domainSemantics": "Search input"}},
            "navigateStep": {"id": "open", "action": "navigate", "value": "{{parameters.baseUrl}}/search/people"},
            "textStep": {"id": "check-results", "action": "checkText", "target": "pageContent", "value": "Results", "timeoutMs": 30000},
            "networkStep": {"id": "wait-get", "action": "awaitNetwork", "match": {"method": "GET"}},
            "textAssertion": {"id": "final-state", "kind": "text", "target": "pageContent", "expected": "Search teams"},
        },
    }


def validate_browser_payload(browser: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    targets = browser.get("targets") if isinstance(browser.get("targets"), dict) else {}
    for alias, bundle in targets.items():
        if not isinstance(bundle, dict):
            blockers.append(f"browser.targets.{alias} must be an object.")
            continue
        blockers.extend(_validate_target_bundle(str(alias), bundle))

    for index, step in enumerate(_list(browser.get("steps")), start=1):
        blockers.extend(_validate_step(step, index, targets))

    for index, assertion in enumerate(_list(browser.get("assertions")), start=1):
        blockers.extend(_validate_assertion(assertion, index, targets))
    return blockers


def _validate_target_bundle(alias: str, bundle: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    primary_signals = [key for key in TARGET_SIGNAL_KEYS if _has_value(bundle.get(key))]
    if not primary_signals:
        blockers.append(f"browser.targets.{alias} must define one selector signal: testId, label, text, css, semanticLocator, or all.")
    if len(primary_signals) > 1:
        blockers.append(
            f"browser.targets.{alias} defines multiple primary selector signals ({', '.join(primary_signals)}). "
            "Use one signal only, or use all for same-element composition."
        )
    if "all" in primary_signals:
        entries = bundle.get("all")
        if not isinstance(entries, list) or len(entries) < 2:
            blockers.append(f"browser.targets.{alias}.all must be an array with at least two entries.")
        else:
            for index, entry in enumerate(entries, start=1):
                if not isinstance(entry, dict):
                    blockers.append(f"browser.targets.{alias}.all[{index}] must be an object.")
                    continue
                signals = [key for key in ("testId", "css") if _has_value(entry.get(key))]
                unsupported = sorted(key for key in entry if key not in {"testId", "css"})
                if unsupported:
                    blockers.append(f"browser.targets.{alias}.all[{index}] uses unsupported signals: {', '.join(unsupported)}.")
                if len(signals) != 1:
                    blockers.append(f"browser.targets.{alias}.all[{index}] must contain exactly one supported signal.")
    return blockers


def _validate_step(step: Any, index: int, targets: dict[str, Any]) -> list[str]:
    if not isinstance(step, dict):
        return [f"browser.steps[{index}] must be an object."]
    blockers: list[str] = []
    step_id = str(step.get("id") or f"#{index}")
    action = step.get("action")
    if action not in VALID_BROWSER_ACTIONS:
        blockers.append(
            f"Unsupported browser step action at {step_id}: {action!r}. Valid actions: {', '.join(sorted(VALID_BROWSER_ACTIONS))}."
        )
        return blockers

    if action == "navigate":
        if not isinstance(step.get("value"), str) or not step.get("value"):
            blockers.append(f"Step {step_id} action navigate must put the URL in value, not target.")
        return blockers

    if action in {"click", "fill", "select", "waitForText", "checkText", "scrollIntoView"}:
        blockers.extend(_require_named_target(step, step_id, targets))
    if action in {"fill", "select", "waitForText", "checkText", "checkLocation"} and not isinstance(step.get("value"), str):
        blockers.append(f"Step {step_id} action {action} requires string value.")
    if action == "awaitNetwork":
        blockers.extend(_validate_network_match(step.get("match"), f"Step {step_id}"))
    if action == "repeatUntil":
        if not isinstance(step.get("until"), dict):
            blockers.append(f"Step {step_id} action repeatUntil requires until object.")
        if not isinstance(step.get("do"), dict):
            blockers.append(f"Step {step_id} action repeatUntil requires do object.")
    return blockers


def _validate_assertion(assertion: Any, index: int, targets: dict[str, Any]) -> list[str]:
    if not isinstance(assertion, dict):
        return [f"browser.assertions[{index}] must be an object."]
    blockers: list[str] = []
    assertion_id = str(assertion.get("id") or f"#{index}")
    kind = assertion.get("kind")
    if kind not in VALID_ASSERTION_KINDS:
        blockers.append(
            f"Unsupported browser assertion kind at {assertion_id}: {kind!r}. Valid kinds: {', '.join(sorted(VALID_ASSERTION_KINDS))}."
        )
        return blockers
    if kind in {"text", "visible", "hidden"}:
        blockers.extend(_require_named_target(assertion, f"Assertion {assertion_id}", targets))
    if kind in {"text", "location"}:
        if "expected" not in assertion:
            if "value" in assertion:
                blockers.append(f"Assertion {assertion_id} uses value; browser assertions require expected.")
            else:
                blockers.append(f"Assertion {assertion_id} kind {kind} requires expected.")
    return blockers


def _validate_network_match(match: Any, prefix: str) -> list[str]:
    if not isinstance(match, dict):
        return [f"{prefix} action awaitNetwork requires match object."]
    present_keys = {str(key) for key, value in match.items() if value is not None}
    unsupported = sorted(present_keys - VALID_NETWORK_MATCH_KEYS)
    blockers = []
    if unsupported:
        blockers.append(f"{prefix} awaitNetwork.match uses unsupported keys: {', '.join(unsupported)}.")
    if not present_keys:
        blockers.append(f"{prefix} awaitNetwork.match must include at least one supported field.")
    return blockers


def _require_named_target(item: dict[str, Any], label: str, targets: dict[str, Any]) -> list[str]:
    target = item.get("target")
    if not isinstance(target, str) or not target:
        return [f"{label} requires target referencing a browser.targets alias."]
    if target not in targets:
        return [f"{label} target {target!r} is not declared in browser.targets."]
    return []


def _has_value(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) or isinstance(value, list) and bool(value)


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
