from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.integrations.manifests import load_all_states
from proofsignal_spec.runtime.resolver import ensure_core_runtime
from proofsignal_spec.workspace import layout
from proofsignal_spec.workspace.repository import init_workspace
from proofsignal_spec.workspace.validation import validate_workspace


def run(project: Path, core_cmd: str | None = None) -> dict[str, Any]:
    workspace_exists = layout.workspace_root(project).exists()
    if workspace_exists and core_cmd:
        init_workspace(project, core_cmd=core_cmd)
    findings = validate_workspace(project) if workspace_exists else [{"severity": "blocking", "code": "workspace-missing", "message": "Run `proofsignal-spec init` first."}]
    runtime = ensure_core_runtime(project, explicit_core_cmd=core_cmd, context="check")
    core = {
        "available": runtime.status == "ready",
        "compatible": runtime.status == "ready",
        "message": runtime.message,
        "proofsignalVersion": runtime.runtimeVersion,
        "contractVersion": runtime.contractVersion,
        "missingOperations": runtime.missingOperations,
        "incompatibleOperations": runtime.incompatibleOperations,
    }
    integrations = load_all_states(project).get("integrations", {}) if workspace_exists else {}
    status = "passed" if workspace_exists and not any(item.get("severity") == "blocking" for item in findings) and runtime.status == "ready" else "blocked"
    return {
        "schemaVersion": "proofsignal-spec-check/v1",
        "status": status,
        "workspace": {"exists": workspace_exists, "path": str(layout.workspace_root(project)), "findings": findings},
        "managedRuntimeReadiness": runtime.to_dict(),
        "core": core,
        "integrations": integrations,
    }
