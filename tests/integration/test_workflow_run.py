from __future__ import annotations

import builtins
import json

from proofsignal_spec.commands import run as run_command
from proofsignal_spec.workspace.models import ArtifactReference, RuntimeInputRequirement, UseCaseRecord
from proofsignal_spec.workspace.repository import init_workspace
from proofsignal_spec.workspace.repository import save_use_case
from proofsignal_spec.workflows.engine import create_workflow_run, generate_tasks, implement_artifacts, plan_artifacts, validate_stage


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
