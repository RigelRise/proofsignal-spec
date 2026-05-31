from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.commands.integration import install as install_integration
from proofsignal_spec.core.adapter import readiness
from proofsignal_spec.workflows.core_setup import run_core_setup
from proofsignal_spec.workspace.repository import init_workspace


def run(project: Path, integration: str, force: bool = False, core_cmd: str | None = None) -> dict[str, Any]:
    workspace = init_workspace(project, force=False)
    core_setup = run_core_setup(project, explicit_core_cmd=core_cmd) if core_cmd else run_core_setup(project)
    workspace = init_workspace(project, force=False)
    installed = install_integration(project, integration, force=force, default=True)
    if core_setup.status == "ready":
        core = readiness(executable=core_setup.coreCommand, cwd=project)
    else:
        core = {
            "available": False,
            "compatible": False,
            "message": core_setup.message,
            "missingOperations": core_setup.missingOperations,
            "incompatibleOperations": core_setup.incompatibleOperations,
        }
    return {
        "workspacePath": str(project / ".proofsignal"),
        "workspace": workspace,
        "integration": installed["integration"]["key"],
        "installedFiles": installed["installedFiles"],
        "coreSetup": core_setup.to_dict(),
        "core": core,
        "next": "Run `/proofsignal-understand` in your agent, or use `proofsignal-spec workflow run proofsignal-use-case --goal \"<behavior>\"`.",
    }
