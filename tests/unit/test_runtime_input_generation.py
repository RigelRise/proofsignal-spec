from __future__ import annotations

import re

import pytest

from proofsignal_spec.commands.runtime_inputs import resolve_runtime_inputs
from proofsignal_spec.core.errors import RuntimeInputError
from proofsignal_spec.workspace.models import RuntimeInputRequirement


def test_generated_runtime_input_resolves_at_run_time_and_reuses_value() -> None:
    requirement = RuntimeInputRequirement.from_dict(
        {"name": "resourceName", "source": "generated", "template": "ProofSignal {{run.shortId}}"}
    )

    first = resolve_runtime_inputs([requirement], interactive=False, run_id="run-one")
    second = resolve_runtime_inputs([requirement], interactive=False, run_id="run-two")

    assert first["resourceName"] == "ProofSignal runone"
    assert second["resourceName"] == "ProofSignal runtwo"
    assert first["resourceName"] != second["resourceName"]


def test_generated_runtime_input_secret_looking_name_is_blocked() -> None:
    requirement = RuntimeInputRequirement.from_dict(
        {"name": "apiToken", "source": "generated", "template": "ProofSignal {{run.shortId}}"}
    )

    with pytest.raises(RuntimeInputError, match=re.escape("runtime input name looks secret-bearing")):
        resolve_runtime_inputs([requirement], interactive=False, run_id="run-one")

