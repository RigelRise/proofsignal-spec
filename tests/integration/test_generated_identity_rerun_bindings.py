from __future__ import annotations

from verifysignal_spec.workspace.models import RunHistoryEntry
from verifysignal_spec.workspace.repository import load_document, load_use_case, record_run, resolve_named_output, save_use_case

from tests.fixtures.workflows.side_effect_contract_alignment import create_write_policy_workspace


def test_committed_run_publishes_named_output_and_committed_binding(tmp_path) -> None:
    record = create_write_policy_workspace(tmp_path)
    entry = _run_entry(post_commit=True, binding_status="committed", output_value="/project/verifysignal-a")

    record_run(tmp_path, entry)

    saved = load_use_case(tmp_path, "add-collaboration-project").lastRun
    assert saved["resolvedRuntimeInputs"][0]["status"] == "committed"
    assert resolve_named_output(tmp_path, "createdProjectUrl")["value"] == "/project/verifysignal-a"


def test_pre_commit_failure_discards_generated_binding_and_does_not_publish_named_output(tmp_path) -> None:
    create_write_policy_workspace(tmp_path)
    entry = _run_entry(post_commit=False, binding_status="discarded", output_value="/project/should-not-publish", status="failed")

    record_run(tmp_path, entry)

    saved = load_use_case(tmp_path, "add-collaboration-project").lastRun
    assert saved["resolvedRuntimeInputs"][0]["status"] == "discarded"
    assert load_document(tmp_path / ".verifysignal/named-outputs.yaml", default={"outputs": []})["outputs"] == []


def _run_entry(*, post_commit: bool, binding_status: str, output_value: str, status: str = "passed") -> RunHistoryEntry:
    return RunHistoryEntry(
        runId=f"run-{binding_status}",
        useCaseAlias="add-collaboration-project",
        profile="normal",
        status=status,
        coreStatus="passed" if status == "passed" else "failed",
        coverageStatus="complete" if status == "passed" else "not-run",
        runtimeOutputs=[{"name": "createdProjectUrl", "source": "finalUrl", "status": "captured", "value": output_value}],
        resolvedRuntimeInputs=[
            {
                "name": "projectTitle",
                "value": f"VerifySignal {binding_status}",
                "source": "generated",
                "runId": f"run-{binding_status}",
                "useCaseAlias": "add-collaboration-project",
                "targetScope": "https://example.test",
                "refreshed": True,
                "committed": post_commit,
                "status": binding_status,
            }
        ],
        postCommitInterpretation={
            "postCommit": post_commit,
            "sideEffectMayExist": post_commit,
            "sideEffectStatus": "committed-confirmed" if post_commit else "not-started",
            "failurePhase": "post-commit" if post_commit else "pre-commit",
            "rerunRisk": "safe-with-new-inputs" if post_commit else "safe",
        },
        startedAt="2026-06-18T00:00:00Z",
        completedAt="2026-06-18T00:00:01Z",
    )
