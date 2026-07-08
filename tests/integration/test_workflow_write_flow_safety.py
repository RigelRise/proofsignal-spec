from __future__ import annotations

import json

from verifysignal_spec.commands.validate import run as validate_run
from verifysignal_spec.workspace.models import ArtifactReference, RuntimeInputRequirement, UseCaseRecord
from verifysignal_spec.workspace.repository import init_workspace, save_use_case
from tests.integration.test_workflow_run import _write_minimal_artifacts


def test_write_draft_can_exist_but_readiness_blocks_without_core_guardrails(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("VERIFYSIGNAL_CORE_CMD", str(FAKE_CORE))
    monkeypatch.setenv("FAKE_VERIFYSIGNAL_MODE", "contracts-missing-side-effect-guardrails")
    init_workspace(tmp_path, core_cmd=str(FAKE_CORE))
    _write_minimal_artifacts(tmp_path, "create-resource", parameters={"baseUrl": "https://example.test"})
    save_use_case(
        tmp_path,
        UseCaseRecord(
            alias="create-resource",
            title="Create Resource",
            description="Create resource.",
            runRequest=ArtifactReference(path=".verifysignal/run-requests/create-resource.yaml", kind="run-request", id="request.create-resource", version="1.0.0"),
            mainSkill=ArtifactReference(path=".verifysignal/skills/create-resource.browser.md", kind="skill", id="skill.create-resource", version="1.0.0"),
            skills=[ArtifactReference(path=".verifysignal/skills/create-resource.browser.md", kind="skill", id="skill.create-resource", version="1.0.0")],
            runtimeInputs=[RuntimeInputRequirement(name="baseUrl", source="default", value="https://example.test")],
            sideEffects={
                "class": "write",
                "commitStepId": "submit-resource",
                "allowed": [{"id": "create-resource", "kind": "network", "methods": ["POST"], "urlContains": "/resources"}],
            },
            rerunPolicy={"afterNoCommit": "allowed", "afterCommit": "blocked"},
        ),
    )

    result = validate_run(tmp_path, "create-resource", runtime_readiness=True, core_cmd=str(FAKE_CORE))

    assert result["status"] == "blocked"
    assert "runtime.side-effect-core-contract-missing" in result["runtimeReadiness"]["findingIds"]


def test_side_effect_policy_and_runtime_outputs_render_in_run_request(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE
    from verifysignal_spec.workspace import artifacts

    monkeypatch.setenv("VERIFYSIGNAL_CORE_CMD", str(FAKE_CORE))
    init_workspace(tmp_path, core_cmd=str(FAKE_CORE))
    record = UseCaseRecord(
        alias="create-resource",
        title="Create Resource",
        description="Create resource.",
        runRequest=ArtifactReference(path=".verifysignal/run-requests/create-resource.yaml", kind="run-request", id="request.create-resource", version="1.0.0"),
        mainSkill=ArtifactReference(path=".verifysignal/skills/create-resource.browser.md", kind="skill", id="skill.create-resource", version="1.0.0"),
        skills=[ArtifactReference(path=".verifysignal/skills/create-resource.browser.md", kind="skill", id="skill.create-resource", version="1.0.0")],
        runtimeInputs=[RuntimeInputRequirement(name="resourceName", source="generated", template="VerifySignal {{run.shortId}}")],
        sideEffects={
            "class": "write",
            "mode": "enforce",
            "commitStepId": "submit-resource",
            "allowed": [{"id": "create-resource", "kind": "network", "methods": ["POST"], "urlContains": "/resources"}],
        },
        runtimeOutputs=[{"name": "createdResourceUrl", "source": "finalUrl"}],
        rerunPolicy={"afterNoCommit": "allowed", "afterCommit": "blocked"},
    )

    rendered = json.loads(artifacts.render_run_request(record))

    assert rendered["sideEffectPolicy"]["class"] == "write"
    assert rendered["sideEffectPolicy"]["mode"] == "enforce"
    assert rendered["runtimeOutputs"] == [{"name": "createdResourceUrl", "source": "finalUrl"}]
    assert rendered["runtimeInputs"][0]["source"] == "generated"
    assert "resourceName" not in rendered["parameters"]
