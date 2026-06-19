from __future__ import annotations

from proofsignal_spec.commands.runtime_inputs import resolve_runtime_inputs
from proofsignal_spec.workspace.models import RuntimeInputRequirement


def test_refresh_generates_new_value_not_seed_literal() -> None:
    requirement = RuntimeInputRequirement(
        name="projectTitle",
        source="generated",
        value="ProofSignal collab seed",
        refreshOnRerunAfterCommit=True,
    )

    values = resolve_runtime_inputs(
        [requirement],
        interactive=False,
        run_id="add-collaboration-project-20260618T120000Z",
        refresh_names=["projectTitle"],
    )

    assert values["projectTitle"] != "ProofSignal collab seed"
    assert values["projectTitle"].startswith("ProofSignal collab seed ")


def test_generated_binding_resolves_once_for_same_run() -> None:
    requirement = RuntimeInputRequirement(
        name="projectTitle",
        source="generated",
        template="{{seed}} {{run.shortId}}",
        value="ProofSignal collab seed",
    )

    first = resolve_runtime_inputs([requirement], interactive=False, run_id="run-one")
    second = resolve_runtime_inputs([requirement], interactive=False, run_id="run-one")

    assert first["projectTitle"] == second["projectTitle"]
