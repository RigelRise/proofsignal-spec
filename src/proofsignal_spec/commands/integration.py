from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.integrations.claude import ClaudeIntegration
from proofsignal_spec.integrations.codex import CodexIntegration
from proofsignal_spec.integrations.manifests import install_rendered_files, load_all_states, remove_integration, set_default

INTEGRATIONS = {
    "codex": CodexIntegration,
    "claude": ClaudeIntegration,
}


def get_integration(key: str):
    if key not in INTEGRATIONS:
        raise ValueError(f"Unsupported integration: {key}")
    return INTEGRATIONS[key]()


def install(project: Path, key: str, force: bool = False, default: bool = True) -> dict[str, Any]:
    integration = get_integration(key)
    state = install_rendered_files(
        project,
        integration.key,
        integration.display_name,
        integration.invoke_style,
        integration.render_files(project),
        force=force,
        default=default,
    )
    return {"integration": state.to_dict(), "installedFiles": [item.path for item in state.managedFiles]}


def list_integrations(project: Path) -> dict[str, Any]:
    state = load_all_states(project)
    installed = state.get("integrations", {})
    return {
        "available": [{"key": key, "displayName": cls.display_name} for key, cls in INTEGRATIONS.items()],
        "installed": installed,
    }


def use(project: Path, key: str) -> dict[str, Any]:
    set_default(project, key)
    return {"default": key}


def upgrade(project: Path, key: str | None = None, force: bool = False) -> dict[str, Any]:
    keys = [key] if key else list(INTEGRATIONS)
    results = []
    for item in keys:
        results.append(install(project, item, force=force, default=False))
    return {"upgraded": results}


def remove(project: Path, key: str, force: bool = False) -> dict[str, Any]:
    preserved = remove_integration(project, key, force=force)
    return {"removed": key, "preserved": preserved}
