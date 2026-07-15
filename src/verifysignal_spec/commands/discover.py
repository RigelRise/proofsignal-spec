from __future__ import annotations

from pathlib import Path
from typing import Any

from verifysignal_spec.core.adapter import CoreAdapter
from verifysignal_spec.runtime.resolver import ensure_core_runtime


def run(
    project: Path,
    url: str,
    skill: Path,
    *,
    core_cmd: str | None = None,
    api_base_url: str | None = None,
) -> dict[str, Any]:
    """Ground a drafted skill's targets against the live DOM via Core's `discover`.

    Routes through the shared managed runtime resolver like every other
    Core-dependent command, instead of constructing a Core adapter from an
    explicit/persisted command and falling back to a literal ``verifysignal`` on
    ``PATH``. ``discover`` is Core's entitlement-free operation, so with no token
    or receipt present the resolver performs compatibility and capability
    negotiation without requiring entitlement.
    """
    managed_runtime = ensure_core_runtime(
        project,
        explicit_core_cmd=core_cmd,
        api_base_url=api_base_url,
        context="discover",
    )
    if managed_runtime.status != "ready":
        return _runtime_setup_blocked_payload(managed_runtime)
    return CoreAdapter(executable=managed_runtime.runtimeCommand, cwd=project).discover(url=url, skill=skill)


def _runtime_setup_blocked_payload(managed_runtime: Any) -> dict[str, Any]:
    runtime_payload = managed_runtime.to_dict()
    is_core_missing = any(blocker.get("code") == "core.missing" for blocker in runtime_payload.get("blockers", []))
    return {
        "status": "blocked",
        "message": "Discover requires a resolved VerifySignal Core runtime; Core setup is required."
        if is_core_missing
        else "Discover requires a resolved VerifySignal Core runtime.",
        "managedRuntimeReadiness": runtime_payload,
        "blockers": runtime_payload.get("blockers", []),
        "nextCommand": managed_runtime.nextAction,
    }
