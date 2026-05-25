from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.commands.integration import install as install_integration
from proofsignal_spec.core.adapter import readiness
from proofsignal_spec.workspace.repository import init_workspace


def run(project: Path, integration: str, force: bool = False, core_cmd: str | None = None) -> dict[str, Any]:
    workspace = init_workspace(project, force=False, core_cmd=core_cmd)
    installed = install_integration(project, integration, force=force, default=True)
    core = readiness(executable=core_cmd, cwd=project)
    return {
        "workspacePath": str(project / ".proofsignal"),
        "workspace": workspace,
        "integration": installed["integration"]["key"],
        "installedFiles": installed["installedFiles"],
        "core": core,
        "next": "Run `/proofsignal-understand` in your agent, or use `proofsignal-spec workflow run proofsignal-use-case --goal \"<behavior>\"`.",
    }
