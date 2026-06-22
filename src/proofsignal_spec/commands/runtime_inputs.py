from __future__ import annotations

import getpass
import os
import re
from typing import Any

from proofsignal_spec.core.errors import RuntimeInputError
from proofsignal_spec.workspace.models import RuntimeInputRequirement
from proofsignal_spec.workspace.validation import looks_secret, runtime_input_name_looks_secret


def resolve_runtime_inputs(
    requirements: list[RuntimeInputRequirement],
    interactive: bool = True,
    provided: dict[str, Any] | None = None,
    *,
    run_id: str | None = None,
    refresh_names: list[str] | set[str] | None = None,
) -> dict[str, str]:
    provided = {str(key): value for key, value in (provided or {}).items() if value is not None and value != ""}
    values: dict[str, str] = {}
    refresh_set = {str(name) for name in (refresh_names or set())}
    for requirement in requirements:
        if requirement.kind == "credential":
            continue
        value = None
        if requirement.source == "generated":
            if runtime_input_name_looks_secret(requirement.name):
                raise RuntimeInputError(f"Generated runtime input name looks secret-bearing: {requirement.name}")
            seed = requirement.default or requirement.value
            template = requirement.template
            if not template:
                template = f"{seed} {{{{run.shortId}}}}" if seed else "{{run.shortId}}"
            value = _render_generated_template(template, run_id=run_id, seed=seed)
            if looks_secret(value, requirement.name):
                raise RuntimeInputError(f"Generated runtime input value for {requirement.name} looks secret-bearing.")
        elif requirement.source == "environment" and requirement.envVar:
            value = os.environ.get(requirement.envVar)
        elif requirement.envVar:
            value = os.environ.get(requirement.envVar)
        if value is None and requirement.name in provided:
            value = provided[requirement.name]
        if value is None and requirement.source == "default":
            value = ""
        if value is None and interactive:
            prompt = requirement.description or f"Value for {requirement.name}: "
            if requirement.kind == "credential":
                value = getpass.getpass(prompt)
            else:
                value = input(prompt)
        if requirement.required and value in {None, ""}:
            raise RuntimeInputError(f"Missing required runtime input: {requirement.name}")
        if value not in {None, ""}:
            values[requirement.name] = str(value)
            if requirement.name in refresh_set:
                values[requirement.name] = str(value)
    return values


def _render_generated_template(template: str, *, run_id: str | None, seed: str | None = None) -> str:
    normalized_run_id = run_id or "run"
    replacements = {
        "run.id": normalized_run_id,
        "run.shortId": _short_id(normalized_run_id),
        "seed": seed or "",
    }
    value = template
    for key, replacement in replacements.items():
        value = value.replace("{{" + key + "}}", replacement)
        value = value.replace("{{ " + key + " }}", replacement)
    return value


def _short_id(run_id: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]", "", run_id).lower()
    return cleaned[-12:] or "run"
