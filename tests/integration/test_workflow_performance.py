from __future__ import annotations

import time

from proofsignal_spec.workspace.repository import init_workspace
from proofsignal_spec.workflows.readiness import validation_readiness
from proofsignal_spec.workflows.engine import create_workflow_run, generate_tasks, implement_artifacts, plan_artifacts, specify, workflow_list
from proofsignal_spec.workflows.prerequisites import check_prerequisites


def test_workflow_status_list_handles_50_runs_under_one_second(tmp_path) -> None:
    init_workspace(tmp_path)
    for index in range(50):
        create_workflow_run(tmp_path, f"Validate behavior {index}.", alias=f"case-{index}", integration="codex")
    started = time.monotonic()
    result = workflow_list(tmp_path)
    elapsed = time.monotonic() - started
    assert len(result["runs"]) == 50
    assert elapsed < 1.0


def test_representative_workflow_checks_complete_under_one_second(tmp_path) -> None:
    init_workspace(tmp_path)
    create_workflow_run(tmp_path, "Validate login.", alias="login", integration="codex")
    specify(tmp_path, "login", "Validate login.")
    plan_artifacts(tmp_path, "login")
    generate_tasks(tmp_path, "login")
    implement_artifacts(tmp_path, "login")

    started = time.monotonic()
    results = [
        check_prerequisites(tmp_path, "specify"),
        check_prerequisites(tmp_path, "clarify", alias="login"),
        check_prerequisites(tmp_path, "tasks", alias="login"),
        check_prerequisites(tmp_path, "validate", alias="login"),
    ]
    elapsed = time.monotonic() - started
    assert [result["status"] for result in results] == ["ready", "ready", "ready", "ready"]
    assert elapsed < 1.0


def test_validation_readiness_check_completes_under_one_second_without_core(tmp_path) -> None:
    init_workspace(tmp_path, core_cmd="missing-proofsignal-core-for-test")
    create_workflow_run(tmp_path, "Validate login.", alias="login", integration="codex")
    specify(tmp_path, "login", "Validate login.")
    plan_artifacts(tmp_path, "login")
    generate_tasks(tmp_path, "login")
    implement_artifacts(tmp_path, "login")

    started = time.monotonic()
    result = validation_readiness(tmp_path, alias="login")
    elapsed = time.monotonic() - started
    assert result["schemaVersion"] == "proofsignal-spec-validation-readiness/v1"
    assert elapsed < 1.0
