from __future__ import annotations

from proofsignal_spec.workspace.repository import init_workspace
from proofsignal_spec.workflows.models import WorkflowRun
from proofsignal_spec.workflows.repository import load_workflow_run, save_workflow_run, workflow_dir_rel


def test_workflow_run_persists_under_workspace(tmp_path) -> None:
    init_workspace(tmp_path)
    run = WorkflowRun(runId="wf-test", useCaseAlias="login", workflowDir=workflow_dir_rel(tmp_path, "login"))
    save_workflow_run(tmp_path, run)
    loaded = load_workflow_run(tmp_path, "wf-test")
    assert loaded.runId == "wf-test"
    assert loaded.workflowDir == ".proofsignal/workflows/use-cases/login"
