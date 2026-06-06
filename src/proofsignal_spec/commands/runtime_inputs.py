from __future__ import annotations

import getpass
import os
from typing import Any

from proofsignal_spec.core.errors import RuntimeInputError
from proofsignal_spec.workspace.models import RuntimeInputRequirement


def resolve_runtime_inputs(
    requirements: list[RuntimeInputRequirement],
    interactive: bool = True,
    provided: dict[str, Any] | None = None,
) -> dict[str, str]:
    provided = {str(key): value for key, value in (provided or {}).items() if value is not None and value != ""}
    values: dict[str, str] = {}
    for requirement in requirements:
        if requirement.kind == "credential":
            continue
        value = None
        if requirement.source == "environment" and requirement.envVar:
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
    return values
