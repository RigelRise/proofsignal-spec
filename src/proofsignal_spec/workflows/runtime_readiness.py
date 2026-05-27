from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from proofsignal_spec.workspace.repository import load_document, load_use_case

from .models import RuntimeReadinessCheck


ReachabilityChecker = Callable[[str], bool]


def evaluate_runtime_readiness(
    project: Path,
    alias: str,
    *,
    authoring_result: dict[str, Any] | None = None,
    reachability_checker: ReachabilityChecker | None = None,
) -> RuntimeReadinessCheck:
    """Evaluate bounded runtime readiness without executing the browser flow."""

    record = load_use_case(project, alias)
    locator = _resolved_target_locator(project, record)
    findings: list[str] = []

    target_resolution = "resolved" if locator else "unresolved"
    if not locator:
        findings.append("runtime.target-unresolved")

    missing_inputs = _missing_required_parameter_inputs(project, record)
    prerequisite_status = "missing" if missing_inputs else "complete"
    findings.extend(f"runtime.prerequisite-missing.{name}" for name in missing_inputs)
    if locator:
        findings.extend(
            f"runtime.stage-handoff-defect.{name}-empty-after-resolution"
            for name in missing_inputs
            if name.lower() in {"baseurl", "targeturl", "url"}
        )

    reachability_status = "unchecked"
    if locator:
        reachable = (reachability_checker or _syntactic_reachability)(locator)
        reachability_status = "reachable" if reachable else "unreachable"
        if not reachable:
            findings.append("runtime.target-unreachable")

    authoring_status = _authoring_status(authoring_result)
    if authoring_status in {"failed", "blocked"}:
        findings.append("runtime.authoring-readiness-blocked")

    status = "passed"
    if target_resolution != "resolved" or prerequisite_status != "complete" or reachability_status == "unreachable":
        status = "blocked"
    elif authoring_status in {"failed", "blocked"}:
        status = "blocked"

    return RuntimeReadinessCheck(
        useCaseAlias=alias,
        targetResolutionStatus=target_resolution,
        targetReachabilityStatus=reachability_status,
        requiredPrerequisiteStatus=prerequisite_status,
        authoringReadinessStatus=authoring_status,
        fullBrowserFlowExecuted=False,
        status=status,
        findingIds=findings,
        targetLocator=locator,
        message=_message(status, findings),
    )


def _resolved_target_locator(project: Path, record: Any) -> str | None:
    run_request = _run_request_document(project, record)
    parameters = run_request.get("parameters") if isinstance(run_request, dict) else {}
    if isinstance(parameters, dict):
        for key in ["baseUrl", "targetUrl", "url"]:
            value = parameters.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    workflow = record.workflow if isinstance(record.workflow, dict) else {}
    for decision in workflow.get("stageHandoffDecisions", []):
        if not isinstance(decision, dict):
            continue
        key = decision.get("key") or decision.get("id") or decision.get("kind")
        status = str(decision.get("status", "active"))
        if key in {"browserTargetEnvironment", "browser-target-environment"} and status in {"active", "resolved"}:
            value = str(decision.get("valueSummary") or decision.get("locator") or "").strip()
            nested = decision.get("value") if isinstance(decision.get("value"), dict) else {}
            value = value or str(nested.get("locator") or nested.get("url") or "").strip()
            if value:
                return value
    return None


def _missing_required_parameter_inputs(project: Path, record: Any) -> list[str]:
    run_request = _run_request_document(project, record)
    parameters = run_request.get("parameters") if isinstance(run_request, dict) else {}
    parameters = parameters if isinstance(parameters, dict) else {}
    missing: list[str] = []
    for item in record.runtimeInputs:
        if not item.required or item.kind != "parameter":
            continue
        value = parameters.get(item.name)
        if value is None or value == "":
            missing.append(item.name)
    return missing


def _run_request_document(project: Path, record: Any) -> dict[str, Any]:
    if not record.runRequest:
        return {}
    try:
        data = load_document(project / record.runRequest.path, default={})
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _syntactic_reachability(locator: str) -> bool:
    parsed = urlparse(locator)
    if parsed.scheme in {"http", "https"}:
        return bool(parsed.netloc)
    return bool(locator.strip())


def _authoring_status(authoring_result: dict[str, Any] | None) -> str:
    if not authoring_result:
        return "unchecked"
    status = authoring_result.get("status") or authoring_result.get("data", {}).get("status")
    if status == "passed":
        return "passed"
    if status == "blocked":
        return "blocked"
    if status in {"failed", "error"}:
        return "failed"
    return "failed"


def _message(status: str, findings: list[str]) -> str:
    if status == "passed":
        return "Runtime readiness passed without executing the full browser flow."
    if "runtime.target-unreachable" in findings:
        return "Target environment is not reachable; recover the environment before rewriting artifacts."
    if "runtime.target-unresolved" in findings:
        return "Browser target environment is unresolved."
    return "Runtime readiness is blocked."
