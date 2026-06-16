from __future__ import annotations

import builtins
import json

from proofsignal_spec.commands import run as run_command
from proofsignal_spec.workspace.models import ArtifactReference, RuntimeInputRequirement, UseCaseRecord
from proofsignal_spec.workspace.repository import init_workspace
from proofsignal_spec.workspace.repository import load_use_case, save_use_case
from proofsignal_spec.workflows.engine import create_workflow_run, generate_tasks, implement_artifacts, plan_artifacts, validate_stage
from tests.fixtures.workflows.main_skill_run_coverage import create_main_skill_coverage_workspace


def test_workflow_validate_preserves_core_result(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    init_workspace(tmp_path, core_cmd=str(FAKE_CORE))
    create_workflow_run(tmp_path, "Validate login.", alias="login", integration="codex")
    plan_artifacts(tmp_path, "login")
    generate_tasks(tmp_path, "login")
    implement_artifacts(tmp_path, "login")
    result = validate_stage(tmp_path, "login")
    assert result["core"]["schemaVersion"]


def test_run_uses_run_request_parameters_before_prompting(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    monkeypatch.setattr(builtins, "input", lambda prompt: (_ for _ in ()).throw(AssertionError(f"unexpected prompt: {prompt}")))
    init_workspace(tmp_path, core_cmd=str(FAKE_CORE))
    record = UseCaseRecord(
        alias="login",
        title="Login",
        description="Validate login.",
        runRequest=ArtifactReference(path=".proofsignal/run-requests/login.yaml", kind="run-request", id="request.login", version="1.0.0"),
        mainSkill=ArtifactReference(path=".proofsignal/skills/login.browser.md", kind="skill", id="skill.login", version="1.0.0"),
        skills=[ArtifactReference(path=".proofsignal/skills/login.browser.md", kind="skill", id="skill.login", version="1.0.0")],
        runtimeInputs=[RuntimeInputRequirement(name="baseUrl", description="Target URL")],
    )
    (tmp_path / ".proofsignal/run-requests").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".proofsignal/skills").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".proofsignal/run-requests/login.yaml").write_text(
        json.dumps(
            {
                "schemaVersion": "qa-run-request/v1",
                "request": {"id": "request.login", "name": "Login"},
                "target": "browser",
                "validationScope": "feature-level",
                "skills": [{"id": "skill.login", "version": "1.0.0"}],
                "parameters": {"baseUrl": "https://app.example.test"},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / ".proofsignal/skills/login.browser.md").write_text(
        """# Login

```yaml
schemaVersion: qa-skill/v1
skill:
  id: skill.login
  version: 1.0.0
  kind: browser
  name: Login
  description: Validate login.
browser:
  steps:
    - id: open
      action: navigate
      value: "{{parameters.baseUrl}}"
  assertions: []
```
""",
        encoding="utf-8",
    )
    save_use_case(tmp_path, record)

    result = run_command.run(tmp_path, "login", interactive=True, core_cmd=str(FAKE_CORE))
    assert result["status"] == "passed"


def test_run_blocks_write_without_side_effect_envelope_before_core_execution(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    init_workspace(tmp_path, core_cmd=str(FAKE_CORE))
    _write_minimal_artifacts(tmp_path, "create-resource", parameters={"baseUrl": "https://example.test"})
    record = UseCaseRecord(
        alias="create-resource",
        title="Create Resource",
        description="Create a resource.",
        runRequest=ArtifactReference(path=".proofsignal/run-requests/create-resource.yaml", kind="run-request", id="request.create-resource", version="1.0.0"),
        mainSkill=ArtifactReference(path=".proofsignal/skills/create-resource.browser.md", kind="skill", id="skill.create-resource", version="1.0.0"),
        skills=[ArtifactReference(path=".proofsignal/skills/create-resource.browser.md", kind="skill", id="skill.create-resource", version="1.0.0")],
        runtimeInputs=[RuntimeInputRequirement(name="baseUrl", source="default", value="https://example.test")],
        sideEffects={"class": "write"},
        sideEffectLifecycle=_manual_cleanup_lifecycle(),
        artifactCapabilities=_current_write_capabilities(),
    )
    save_use_case(tmp_path, record)

    result = run_command.run(tmp_path, "create-resource", interactive=False, core_cmd=str(FAKE_CORE))

    assert result["status"] == "blocked"
    assert any(item["code"] == "runtime.side-effect-envelope-missing" for item in result["blockers"])


def test_run_resolves_generated_inputs_in_ephemeral_request_without_rewriting_authored_intent(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    init_workspace(tmp_path, core_cmd=str(FAKE_CORE))
    authored_request = _write_minimal_artifacts(tmp_path, "create-resource", parameters={"baseUrl": "https://example.test"})
    record = UseCaseRecord(
        alias="create-resource",
        title="Create Resource",
        description="Create a resource.",
        runRequest=ArtifactReference(path=".proofsignal/run-requests/create-resource.yaml", kind="run-request", id="request.create-resource", version="1.0.0"),
        mainSkill=ArtifactReference(path=".proofsignal/skills/create-resource.browser.md", kind="skill", id="skill.create-resource", version="1.0.0"),
        skills=[ArtifactReference(path=".proofsignal/skills/create-resource.browser.md", kind="skill", id="skill.create-resource", version="1.0.0")],
        runtimeInputs=[
            RuntimeInputRequirement(name="baseUrl", source="default", value="https://example.test"),
            RuntimeInputRequirement(name="resourceName", source="generated", template="ProofSignal {{run.shortId}}", refreshOnRerunAfterCommit=True),
        ],
        sideEffects={"class": "none"},
    )
    save_use_case(tmp_path, record)

    result = run_command.run(tmp_path, "create-resource", interactive=False, core_cmd=str(FAKE_CORE))

    assert result["status"] == "passed"
    assert authored_request.read_text(encoding="utf-8") == json.dumps(
        {
            "schemaVersion": "qa-run-request/v1",
            "request": {"id": "request.create-resource", "name": "Create Resource"},
            "target": "browser",
            "validationScope": "feature-level",
            "skills": [{"id": "skill.create-resource", "version": "1.0.0"}],
            "parameters": {"baseUrl": "https://example.test"},
        }
    )
    prepared = list((tmp_path / ".proofsignal/runs/create-resource").glob("*.run-request.json"))
    assert prepared
    assert json.loads(prepared[0].read_text(encoding="utf-8"))["parameters"]["resourceName"].startswith("ProofSignal ")
    assert result["core"]["data"]["args"][1] == str(prepared[0])


def test_run_preserves_post_commit_interpretation_from_public_core_fields(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    monkeypatch.setenv("FAKE_PROOFSIGNAL_MODE", "post-commit-report")
    init_workspace(tmp_path, core_cmd=str(FAKE_CORE))
    _write_minimal_artifacts(tmp_path, "create-resource", parameters={"baseUrl": "https://example.test"})
    record = UseCaseRecord(
        alias="create-resource",
        title="Create Resource",
        description="Create a resource.",
        runRequest=ArtifactReference(path=".proofsignal/run-requests/create-resource.yaml", kind="run-request", id="request.create-resource", version="1.0.0"),
        mainSkill=ArtifactReference(path=".proofsignal/skills/create-resource.browser.md", kind="skill", id="skill.create-resource", version="1.0.0"),
        skills=[ArtifactReference(path=".proofsignal/skills/create-resource.browser.md", kind="skill", id="skill.create-resource", version="1.0.0")],
        runtimeInputs=[RuntimeInputRequirement(name="baseUrl", source="default", value="https://example.test")],
        sideEffects={
            "class": "write",
            "commitStepId": "submit-resource",
            "allowed": [{"id": "create-resource", "kind": "network"}],
        },
        rerunPolicy={"afterNoCommit": "allowed", "afterCommit": "blocked"},
        sideEffectLifecycle=_manual_cleanup_lifecycle(),
        artifactCapabilities=_current_write_capabilities(),
    )
    save_use_case(tmp_path, record)

    result = run_command.run(tmp_path, "create-resource", interactive=False, core_cmd=str(FAKE_CORE))

    assert result["status"] == "failed"
    assert result["postCommitInterpretation"]["postCommit"] is True
    assert result["postCommitInterpretation"]["sideEffectMayExist"] is True
    assert result["postCommitInterpretation"]["failurePhase"] == "post-commit"


def test_second_run_after_post_commit_write_is_blocked_by_rerun_policy(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    init_workspace(tmp_path, core_cmd=str(FAKE_CORE))
    _write_minimal_artifacts(tmp_path, "create-resource", parameters={"baseUrl": "https://example.test"})
    record = UseCaseRecord(
        alias="create-resource",
        title="Create Resource",
        description="Create a resource.",
        runRequest=ArtifactReference(path=".proofsignal/run-requests/create-resource.yaml", kind="run-request", id="request.create-resource", version="1.0.0"),
        mainSkill=ArtifactReference(path=".proofsignal/skills/create-resource.browser.md", kind="skill", id="skill.create-resource", version="1.0.0"),
        skills=[ArtifactReference(path=".proofsignal/skills/create-resource.browser.md", kind="skill", id="skill.create-resource", version="1.0.0")],
        runtimeInputs=[RuntimeInputRequirement(name="baseUrl", source="default", value="https://example.test")],
        sideEffects={
            "class": "write",
            "commitStepId": "submit-resource",
            "allowed": [{"id": "create-resource", "kind": "network"}],
        },
        rerunPolicy={"afterNoCommit": "allowed", "afterCommit": "blocked"},
        sideEffectLifecycle=_manual_cleanup_lifecycle(),
        artifactCapabilities=_current_write_capabilities(),
        lastRun={
            "runId": "previous-run",
            "status": "failed",
            "postCommitInterpretation": {
                "postCommit": True,
                "sideEffectMayExist": True,
                "failurePhase": "post-commit",
                "sideEffectStatus": "likely-committed",
                "rerunRisk": "requires-confirmation",
            },
        },
    )
    save_use_case(tmp_path, record)

    result = run_command.run(tmp_path, "create-resource", interactive=False, core_cmd=str(FAKE_CORE))

    assert result["status"] == "blocked"
    assert result["rerunDecision"]["decision"] == "blocked"
    assert any(item["code"] == "runtime.rerun-policy-blocked" for item in result["blockers"])


def test_rerun_allowed_with_new_inputs_refreshes_declared_generated_value(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    init_workspace(tmp_path, core_cmd=str(FAKE_CORE))
    _write_minimal_artifacts(tmp_path, "create-resource", parameters={"baseUrl": "https://example.test"})
    record = UseCaseRecord(
        alias="create-resource",
        title="Create Resource",
        description="Create a resource.",
        runRequest=ArtifactReference(path=".proofsignal/run-requests/create-resource.yaml", kind="run-request", id="request.create-resource", version="1.0.0"),
        mainSkill=ArtifactReference(path=".proofsignal/skills/create-resource.browser.md", kind="skill", id="skill.create-resource", version="1.0.0"),
        skills=[ArtifactReference(path=".proofsignal/skills/create-resource.browser.md", kind="skill", id="skill.create-resource", version="1.0.0")],
        runtimeInputs=[
            RuntimeInputRequirement(name="baseUrl", source="default", value="https://example.test"),
            RuntimeInputRequirement(name="resourceName", source="generated", template="ProofSignal {{run.shortId}}", refreshOnRerunAfterCommit=True),
        ],
        sideEffects={
            "class": "write",
            "commitStepId": "submit-resource",
            "allowed": [{"id": "create-resource", "kind": "network"}],
        },
        rerunPolicy={"afterNoCommit": "allowed", "afterCommit": "allowed-with-new-inputs", "refreshInputs": ["resourceName"]},
        sideEffectLifecycle=_manual_cleanup_lifecycle(),
        artifactCapabilities=_current_write_capabilities(),
        lastRun={
            "runId": "previous-run",
            "status": "failed",
            "postCommitInterpretation": {
                "postCommit": True,
                "sideEffectMayExist": True,
                "failurePhase": "post-commit",
                "sideEffectStatus": "likely-committed",
                "rerunRisk": "safe-with-new-inputs",
            },
        },
    )
    save_use_case(tmp_path, record)

    result = run_command.run(tmp_path, "create-resource", interactive=False, core_cmd=str(FAKE_CORE))

    assert result["status"] == "passed"
    assert result["rerunDecision"]["decision"] == "allowed-with-new-inputs"
    run_record = load_use_case(tmp_path, "create-resource")
    assert run_record.lastRun
    assert run_record.lastRun["resolvedRuntimeInputs"][0]["name"] == "resourceName"
    assert run_record.lastRun["resolvedRuntimeInputs"][0]["refreshed"] is True


def test_run_summary_shows_missing_required_gates_and_partial_diagnostics(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    monkeypatch.setenv("FAKE_PROOFSIGNAL_MODE", "failed-with-partial")
    create_main_skill_coverage_workspace(tmp_path)

    result = run_command.run(tmp_path, "profile-view-unauth", interactive=False, core_cmd=str(FAKE_CORE))

    assert result["status"] == "failed"
    assert result["partialCoverage"]
    assert sorted(result["missingRequiredGates"]) == ["overview-profile-query", "projects-tab-content"]
    assert any(item["gateId"] == "overview-data-card" and item["status"] == "exercised" for item in result["gateCoverage"])


def test_failed_run_summary_uses_diagnostic_coverage_language(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    monkeypatch.setenv("FAKE_PROOFSIGNAL_MODE", "aborted-activity-wait")
    create_main_skill_coverage_workspace(tmp_path)

    result = run_command.run(tmp_path, "profile-view-unauth", interactive=False, core_cmd=str(FAKE_CORE))

    assert result["coreBrowserStatus"] == "failed"
    assert result["specCoverageStatus"] == "diagnostic"
    assert result["runOutcomeSummary"]["overallStatus"] == "failed"
    assert "diagnostic" in result["reason"]


def test_conditional_gate_not_evaluated_does_not_hard_fail_required_coverage(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    monkeypatch.setenv("FAKE_PROOFSIGNAL_MODE", "full-coverage")
    create_main_skill_coverage_workspace(tmp_path)

    result = run_command.run(tmp_path, "profile-view-unauth", interactive=False, core_cmd=str(FAKE_CORE))

    assert result["status"] == "passed"
    assert result["missingRequiredGates"] == []
    assert any(item["gateId"] == "about-tab-content" and item["status"] == "not-evaluated" for item in result["gateCoverage"])


def _write_minimal_artifacts(tmp_path, alias: str, *, parameters: dict[str, str]) -> object:
    (tmp_path / ".proofsignal/run-requests").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".proofsignal/skills").mkdir(parents=True, exist_ok=True)
    request_path = tmp_path / f".proofsignal/run-requests/{alias}.yaml"
    request_path.write_text(
        json.dumps(
            {
                "schemaVersion": "qa-run-request/v1",
                "request": {"id": f"request.{alias}", "name": alias.replace("-", " ").title()},
                "target": "browser",
                "validationScope": "feature-level",
                "skills": [{"id": f"skill.{alias}", "version": "1.0.0"}],
                "parameters": parameters,
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / f".proofsignal/skills/{alias}.browser.md").write_text(
        f"""# {alias}

```yaml
schemaVersion: qa-skill/v1
skill:
  id: skill.{alias}
  version: 1.0.0
  kind: browser
  name: {alias}
  description: test skill
browser:
  steps:
    - id: open
      action: navigate
      value: "{{{{parameters.baseUrl}}}}"
  assertions: []
```
""",
        encoding="utf-8",
    )
    return request_path


def _manual_cleanup_lifecycle() -> dict[str, object]:
    return {
        "cleanupPolicy": "manual",
        "cleanupRequired": True,
        "trackingIntent": "resource-refs",
        "instructions": "Delete created test resources after validation.",
    }


def _current_write_capabilities() -> dict[str, object]:
    return {
        "capabilities": [
            "explicit-confirmation",
            "generated-runtime-inputs",
            "side-effect-lifecycle",
            "write-activity-interpretation",
        ]
    }
