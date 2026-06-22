from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from proofsignal_spec.workspace.repository import load_document
from proofsignal_spec.workspace.validation import looks_secret
from proofsignal_spec.workflows.write_safety import resolve_confirmation_signal_placeholders


def prepare_run_request_document(
    run_request: Path,
    runtime_values: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], bool]:
    document = load_document(run_request, default={}) or {}
    if not isinstance(document, dict):
        return None, [], False

    prepared = dict(document)
    changed = False
    parameters = prepared.get("parameters") if isinstance(prepared.get("parameters"), dict) else {}
    merged_parameters = {**parameters, **runtime_values}
    if merged_parameters != parameters:
        prepared["parameters"] = merged_parameters
        changed = True

    policy_key = "sideEffectPolicy" if isinstance(prepared.get("sideEffectPolicy"), dict) else "sideEffects"
    policy = prepared.get(policy_key)
    if not isinstance(policy, dict) or not isinstance(policy.get("confirmationSignals"), list):
        return prepared, [], changed

    resolved_signals, findings = resolve_confirmation_signal_placeholders(
        list(policy["confirmationSignals"]),
        merged_parameters,
        path_prefix=f"{policy_key}.confirmationSignals",
        secret_checker=looks_secret,
    )
    if findings:
        return prepared, findings, changed

    if resolved_signals != policy.get("confirmationSignals"):
        next_policy = dict(policy)
        next_policy["confirmationSignals"] = resolved_signals
        prepared[policy_key] = next_policy
        changed = True
    return prepared, [], changed


def write_prepared_run_request(output_dir: Path, run_id: str, document: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    prepared = output_dir / f"{run_id}.run-request.json"
    prepared.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return prepared


def confirmation_placeholder_blockers(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "code": f"runtime.{item.get('code')}",
            "severity": "blocker",
            "category": item.get("category", "side-effect-confirmation"),
            "message": item.get("message"),
            "documentationRef": item.get("path"),
            "recoveryCommand": item.get("recoveryCommand") or "proofsignal workflow check validate --alias <alias> --json",
            "nextAction": item.get("nextAction"),
        }
        for item in findings
    ]
