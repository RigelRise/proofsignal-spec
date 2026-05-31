from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.commands.integration import install as install_integration
from proofsignal_spec.core.adapter import readiness
from proofsignal_spec.runtime.resolver import ensure_core_runtime
from proofsignal_spec.workflows.core_setup import run_core_setup
from proofsignal_spec.workspace.repository import init_workspace


def run(project: Path, integration: str, force: bool = False, core_cmd: str | None = None) -> dict[str, Any]:
    workspace = init_workspace(project, force=False)
    runtime = ensure_core_runtime(project, explicit_core_cmd=core_cmd, context="init")
    core_setup = run_core_setup(project, explicit_core_cmd=core_cmd, persist=False) if core_cmd else run_core_setup(project, persist=False)
    workspace = init_workspace(project, force=False)
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
