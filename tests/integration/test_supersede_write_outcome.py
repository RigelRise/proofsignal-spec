from __future__ import annotations

from proofsignal_spec.commands import workflow as workflow_command
from proofsignal_spec.workspace.repository import load_supersede_reviews, load_use_case, save_use_case
from proofsignal_spec.workflows.prerequisites import check_prerequisites

from tests.fixtures.workflows.prerequisites import create_current_understanding_workspace
from tests.fixtures.workflows.side_effect_contract_alignment import blocked_write_last_run, create_write_policy_workspace, supersede_review_payload
from tests.integration.test_workflow_run_preflight_alignment import _write_minimal_stage_artifacts


def test_supersede_review_unblocks_effective_rerun_without_hand_editing_last_run(tmp_path) -> None:
    create_current_understanding_workspace(tmp_path)
    record = create_write_policy_workspace(tmp_path, last_run=blocked_write_last_run())
    record.status = "ready"
    save_use_case(tmp_path, record)
    _write_minimal_stage_artifacts(tmp_path, "add-collaboration-project")
    assert check_prerequisites(tmp_path, "run", alias="add-collaboration-project")["status"] == "blocked"

    result = workflow_command.supersede_write_outcome(
        tmp_path,
        alias="add-collaboration-project",
        payload=supersede_review_payload(source_run_id="violated-run"),
    )

    assert result["status"] == "persisted"
    assert load_use_case(tmp_path, "add-collaboration-project").lastRun["postCommitInterpretation"]["rerunRisk"] == "blocked"
    assert load_supersede_reviews(tmp_path, "add-collaboration-project")[0].sourceRunId == "violated-run"
    check = check_prerequisites(tmp_path, "run", alias="add-collaboration-project")
    assert check["status"] == "ready"
    assert check["rerunDecision"]["decision"] == "allowed-with-new-inputs"
