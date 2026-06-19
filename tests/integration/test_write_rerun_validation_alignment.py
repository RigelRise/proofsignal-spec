from __future__ import annotations

import pytest

from proofsignal_spec.commands.run import evaluate_rerun_decision
from proofsignal_spec.commands.validate import run as validate_run
from proofsignal_spec.workspace.models import RuntimeInputRequirement, UseCaseRecord


def test_validation_and_run_can_share_same_rerun_decision_evaluator() -> None:
    record = UseCaseRecord(
        alias="create-resource",
        title="Create Resource",
        description="Create resource.",
        runtimeInputs=[
            RuntimeInputRequirement(name="projectTitle", source="generated", refreshOnRerunAfterCommit=True),
        ],
        sideEffects={"class": "write"},
        rerunPolicy={"afterCommit": "allowed-with-new-inputs", "refreshRuntimeInputs": ["projectTitle"]},
        lastRun={
            "postCommitInterpretation": {
                "postCommit": True,
                "sideEffectMayExist": True,
                "rerunRisk": "safe-with-new-inputs",
            }
        },
    )

    decision = evaluate_rerun_decision(record)

    assert decision["decision"] == "allowed-with-new-inputs"
    assert decision["refreshRuntimeInputs"] == ["projectTitle"]


@pytest.mark.parametrize(
    ("core_risk", "spec_after_commit", "expected"),
    [
        ("safe", "allowed", "allowed"),
        ("safe-with-new-inputs", "allowed", "allowed-with-new-inputs"),
        ("safe", "allowed-with-new-inputs", "allowed-with-new-inputs"),
        ("requires-confirmation", "allowed-with-new-inputs", "requires-confirmation"),
        ("blocked", "allowed-with-new-inputs", "blocked"),
    ],
)
def test_validation_run_decision_matrix(core_risk: str, spec_after_commit: str, expected: str) -> None:
    record = UseCaseRecord(
        alias="create-resource",
        title="Create Resource",
        description="Create resource.",
        runtimeInputs=[RuntimeInputRequirement(name="projectTitle", source="generated", refreshOnRerunAfterCommit=True)],
        sideEffects={"class": "write"},
        rerunPolicy={"afterCommit": spec_after_commit, "refreshRuntimeInputs": ["projectTitle"]},
        lastRun={
            "postCommitInterpretation": {
                "postCommit": True,
                "sideEffectMayExist": True,
                "rerunRisk": core_risk,
            }
        },
    )

    assert evaluate_rerun_decision(record)["decision"] == expected


def test_validate_reports_same_rerun_decision_as_run_preflight(tmp_path, monkeypatch) -> None:
    from tests.fixtures.workflows.write_rerun_identity import committed_last_run, write_use_case_record
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    record = write_use_case_record(
        tmp_path,
        rerun_policy={"afterCommit": "allowed-with-new-inputs", "refreshRuntimeInputs": ["projectTitle"]},
        last_run=committed_last_run(),
    )

    result = validate_run(tmp_path, record.alias, runtime_readiness=False, core_cmd=str(FAKE_CORE))

    assert result["rerunDecision"] == evaluate_rerun_decision(record)
