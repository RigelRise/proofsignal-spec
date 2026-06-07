from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from proofsignal_spec.commands.integration import install as install_integration
from proofsignal_spec.core.adapter import readiness, resolve_persistable_core_command
from proofsignal_spec.runtime.entitlement import resolve_entitlement_config
from proofsignal_spec.runtime.resolver import ensure_core_runtime
from proofsignal_spec.workflows.core_setup import run_core_setup
from proofsignal_spec.workspace.repository import init_workspace


def run(project: Path, integration: str, force: bool = False, core_cmd: str | None = None, api_base_url: str | None = None) -> dict[str, Any]:
    entitlement_config = resolve_entitlement_config(api_base_url=api_base_url)
    persisted_api_base_url = entitlement_config.apiBaseUrl if api_base_url or entitlement_config.source == "environment" else None
    workspace = init_workspace(project, force=False, api_base_url=persisted_api_base_url)
    email = os.environ.get("PROOFSIGNAL_EMAIL")
    token = os.environ.get("PROOFSIGNAL_EMAIL_UNLOCK_TOKEN")
    if not token and not email and sys.stdin.isatty():
        email = _prompt("ProofSignal email for runtime unlock: ").strip() or None
    runtime = ensure_core_runtime(
        project,
        explicit_core_cmd=core_cmd,
        api_base_url=persisted_api_base_url,
        email=email,
        token=token,
        integration=integration,
        context="init",
    )
    if runtime.status != "ready" and email and not token and sys.stdin.isatty():
        token = _prompt("ProofSignal email unlock token: ").strip() or None
        if token:
            runtime = ensure_core_runtime(
                project,
                explicit_core_cmd=core_cmd,
                api_base_url=persisted_api_base_url,
                token=token,
                integration=integration,
                context="init",
            )
    workspace_core_cmd = None
    if core_cmd and runtime.status == "ready":
        workspace_core_cmd = resolve_persistable_core_command(runtime.runtimeCommand or core_cmd, cwd=project)
        runtime.runtimeCommand = workspace_core_cmd
    core_setup = run_core_setup(project, explicit_core_cmd=workspace_core_cmd, persist=False) if workspace_core_cmd else run_core_setup(project, persist=False)
    workspace = init_workspace(project, force=False, core_cmd=workspace_core_cmd, api_base_url=persisted_api_base_url)
    installed = install_integration(project, integration, force=force, default=True)
    if runtime.status == "ready":
        core = readiness(executable=runtime.runtimeCommand, cwd=project)
    else:
        core = {
            "available": False,
            "compatible": False,
            "message": runtime.message,
            "missingOperations": runtime.missingOperations,
            "incompatibleOperations": runtime.incompatibleOperations,
        }
    return {
        "status": "passed" if runtime.status == "ready" else "blocked",
        "workspacePath": str(project / ".proofsignal"),
        "workspace": workspace,
        "integration": installed["integration"]["key"],
        "installedFiles": installed["installedFiles"],
        "coreSetup": core_setup.to_dict(),
        "runtime": runtime.to_dict(),
        "managedRuntimeReadiness": runtime.to_dict(),
        "core": core,
        "next": "Run `/proofsignal-specify` in your agent, or use `proofsignal workflow run proofsignal-use-case --goal \"<behavior>\"`.",
    }


def _prompt(message: str) -> str:
    sys.stderr.write(message)
    sys.stderr.flush()
    return input()
