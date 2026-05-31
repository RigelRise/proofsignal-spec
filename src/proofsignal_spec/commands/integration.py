from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.integrations.claude import ClaudeIntegration
from proofsignal_spec.integrations.codex import CodexIntegration
from proofsignal_spec.integrations.base import build_onboarding_guidance
from proofsignal_spec.integrations.manifests import install_rendered_files, load_all_states, remove_integration, set_default
from proofsignal_spec.workflows.core_setup import onboarding_core_status, run_core_setup

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
    core_setup_result = run_core_setup(project)
    core_setup = core_setup_result.to_dict()
    core_status = onboarding_core_status(core_setup_result)
    state = install_rendered_files(
        project,
        integration.key,
        integration.display_name,
        integration.invoke_style,
        integration.render_files(project, core_status=core_status),
        force=force,
        default=default,
    )
    guide_path = ".agents/PROOFSIGNAL_ONBOARDING.md" if integration.key == "codex" else ".claude/PROOFSIGNAL_ONBOARDING.md"
    guide = build_onboarding_guidance(
        integration_key=integration.key,
        display_name=integration.display_name,
        generated_guide_path=guide_path,
        core_status=core_status,
    ).to_dict()
    return {
        "integration": state.to_dict(),
        "installedFiles": [item.path for item in state.managedFiles],
        "coreSetup": core_setup,
        "onboardingGuide": guide,
    }


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
