from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from proofsignal_spec.workflows.write_safety import normalize_side_effect_policy
from proofsignal_spec.workspace import layout
from proofsignal_spec.workspace.repository import load_use_case, save_use_case
from proofsignal_spec.workspace.validation import validate_no_secret_values

SCHEMA_VERSION = "proofsignal-spec-policy-set-result/v1"


def set_policy(
    project: Path,
    alias: str,
    *,
    side_effect_class: str,
    mode: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Set a use case's side-effect policy class WITHOUT round-tripping the implement payload.

    This is the lightweight, granular alternative to re-persisting the whole implement stage
    (the all-or-nothing path that caused parameter zeroing, Bug 2). It mutates only the policy,
    preserving runtimeInputs/skills/credentials, and re-syncs the generated run-request so a
    later `run` honors the new class.
    """
    record = load_use_case(project, alias)
    side_effects = dict(record.sideEffects) if isinstance(record.sideEffects, dict) else {}

    if isinstance(payload, dict):
        normalized_payload, findings = normalize_side_effect_policy(payload)
        blocking = [item for item in findings if item.get("severity") == "blocking"]
        if blocking:
            return _blocked(
                alias,
                [
                    {"code": f"policy.{item.get('code', 'invalid')}", "severity": "blocking", "message": item.get("message", "Invalid side-effect policy.")}
                    for item in blocking
                ],
            )
        side_effects.update(normalized_payload)

    side_effects["class"] = side_effect_class
    if mode is not None:
        side_effects["mode"] = mode
    record.sideEffects = side_effects

    secret_findings = validate_no_secret_values(record.sideEffects, "sideEffects")
    if secret_findings:
        return _blocked(alias, secret_findings)

    if _missing_write_resource_identity(record):
        return _blocked(
            alias,
            [
                {
                    "code": "policy.resource-identity-required",
                    "severity": "blocking",
                    "message": "write and external-notification classes require an explicit resourceIdentity before they can be set.",
                }
            ],
        )

    save_use_case(project, record)
    run_request_synced = _sync_run_request_policy(project, record)

    return {
        "schemaVersion": SCHEMA_VERSION,
        "alias": alias,
        "status": "persisted",
        "sideEffects": record.sideEffects,
        "runRequestSynced": run_request_synced,
        "message": f"Side-effect policy class set to '{side_effect_class}'.",
        "nextAction": f"proofsignal validate {alias} --json",
    }


def _blocked(alias: str, blockers: list[dict[str, Any]]) -> dict[str, Any]:
    return {"schemaVersion": SCHEMA_VERSION, "alias": alias, "status": "blocked", "blockers": blockers}


def _missing_write_resource_identity(record: Any) -> bool:
    side_effects = record.sideEffects if isinstance(record.sideEffects, dict) else {}
    side_effect_class = str(side_effects.get("class") or side_effects.get("sideEffectClass") or "none")
    if side_effect_class not in {"write", "external-notification"}:
        return False
    return not (isinstance(getattr(record, "resourceIdentity", None), dict) and record.resourceIdentity)


def _sync_run_request_policy(project: Path, record: Any) -> bool:
    """Embed the new policy into the generated run-request so a later `run` honors it, surgically
    (only the sideEffectPolicy block changes; skills/params/inputs are untouched)."""
    if not record.runRequest or not getattr(record.runRequest, "path", None):
        return False
    try:
        path = layout.project_relative_path(project, record.runRequest.path)
    except ValueError:
        return False
    if not path.exists() or not path.is_file():
        return False
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    if not isinstance(document, dict):
        return False
    document["sideEffectPolicy"] = normalize_side_effect_policy(record.sideEffects)[0]
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return True
