from __future__ import annotations

from proofsignal_spec.commands import run as run_command
from proofsignal_spec.workspace.repository import load_use_case, run_confirmation_requirements, save_use_case
from tests.fixtures.workflows.live_write_readiness import create_live_write_readiness_workspace


def test_run_blocks_legacy_write_without_lifecycle_until_confirmation(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    create_live_write_readiness_workspace(tmp_path)
    record = load_use_case(tmp_path, "add-collaboration-project")
    record.status = "ready"
    save_use_case(tmp_path, record)

    result = run_command.run(tmp_path, "add-collaboration-project", interactive=False, core_cmd=str(FAKE_CORE))

    assert result["status"] == "blocked"
    assert result["requiresConfirmation"] is True
    assert result["confirmation"]["scope"] in {"missing-side-effect-lifecycle", "legacy-missing-safety-capability"}


def test_run_with_matching_confirmation_reports_lifecycle_summary(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    create_live_write_readiness_workspace(tmp_path)
    record = load_use_case(tmp_path, "add-collaboration-project")
    record.status = "ready"
    record.sideEffectLifecycle = {"cleanupPolicy": "manual", "cleanupRequired": True, "instructions": "Delete the project manually."}
    save_use_case(tmp_path, record)
    confirmation_id = run_confirmation_requirements(tmp_path, load_use_case(tmp_path, "add-collaboration-project"))[0].id

    result = run_command.run(
        tmp_path,
        "add-collaboration-project",
        interactive=False,
        core_cmd=str(FAKE_CORE),
        confirmed_risks=[confirmation_id],
    )

    assert result["status"] == "passed"
    assert result["sideEffectLifecycle"]["cleanupPolicy"] == "manual"
    assert result["postCommitInterpretation"]["sideEffectMayExist"] is True
    assert result["postCommitInterpretation"]["sideEffectStatus"] == "unknown"
