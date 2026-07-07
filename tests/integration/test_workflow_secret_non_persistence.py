from __future__ import annotations

import pytest

from proofsignal_spec.commands.runtime_inputs import resolve_runtime_inputs
from proofsignal_spec.core.errors import RuntimeInputError
from proofsignal_spec.workspace.models import ReadinessSnapshot, RuntimeInputRequirement
from proofsignal_spec.workspace.repository import init_workspace, save_readiness_snapshot
from proofsignal_spec.workspace.validation import validate_workspace
from proofsignal_spec.workflows.stage_persistence import persist_stage
from tests.fixtures.workflows.live_write_readiness import create_live_write_readiness_workspace


def test_generated_runtime_input_secret_like_name_is_rejected_before_persistence() -> None:
    with pytest.raises(RuntimeInputError):
        resolve_runtime_inputs(
            [RuntimeInputRequirement(name="apiToken", source="generated", template="ProofSignal {{run.shortId}}")],
            interactive=False,
            run_id="run-one",
        )


def test_generated_runtime_input_secret_like_value_is_rejected_before_persistence() -> None:
    with pytest.raises(RuntimeInputError):
        resolve_runtime_inputs(
            [RuntimeInputRequirement(name="resourceName", source="generated", template="Bearer abcdefghijklmnopqrstuvwxyz123456")],
            interactive=False,
            run_id="run-one",
        )


def test_credential_readiness_hint_rejects_env_assignment_secret_text(tmp_path) -> None:
    create_live_write_readiness_workspace(tmp_path)

    result = persist_stage(
        tmp_path,
        "clarify",
        alias="brands-search-authenticated",
        payload={
            "questions": [],
            "credentialReadinessHints": [
                {
                    "credentialGroup": "app",
                    "expectedSource": "environment",
                    "requiredRuntimeNames": ["APP_TEST_EMAIL", "APP_TEST_PASSWORD"],
                    "preparationHint": "APP_TEST_PASSWORD=super-secret-password-value",
                }
            ],
        },
    )

    assert result["status"] == "invalid"
    assert result["blockers"][0]["code"] == "payload.invalid"


def test_readiness_snapshot_artifact_fingerprints_are_not_secret_findings(tmp_path) -> None:
    init_workspace(tmp_path)
    save_readiness_snapshot(
        tmp_path,
        ReadinessSnapshot(
            alias="add-collaboration-project",
            status="ready",
            checkedAt="2026-06-17T00:00:00Z",
            artifactFingerprints={
                ".proofsignal/run-requests/add-collaboration-project.yaml": "a" * 64,
                ".proofsignal/skills/validate-add-collaboration-project-flow.browser.md": "b" * 64,
            },
        ),
    )

    findings = validate_workspace(tmp_path)

    assert not any(item["code"] == "secret-looking-value" for item in findings)
