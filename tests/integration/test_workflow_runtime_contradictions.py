from __future__ import annotations

from proofsignal_spec.commands import repair as repair_command
from proofsignal_spec.commands import run as run_command
from proofsignal_spec.workspace.repository import init_workspace

from tests.fixtures.workflows.real_run_guardrails import create_real_run_guardrail_workspace, run_request_payload


def test_missing_planned_gate_is_reported_as_runtime_contradiction(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    init_workspace(tmp_path, core_cmd=str(FAKE_CORE))
    create_real_run_guardrail_workspace(tmp_path)
    (tmp_path / ".proofsignal/run-requests").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".proofsignal/skills").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".proofsignal/run-requests/profile-view-unauth.yaml").write_text(run_request_payload()["content"], encoding="utf-8")
    (tmp_path / ".proofsignal/skills/validate-profile-view-unauth-flow.browser.md").write_text(
        """# Profile

```yaml
schemaVersion: qa-skill/v1
skill:
  id: skill.validate-profile-view-unauth-flow
  version: 1.0.0
  kind: browser
browser:
  targets:
    profileName:
      css: h2
      domainSemantics: Profile name
  steps:
    - id: open
      action: navigate
      value: "{{parameters.baseUrl}}/profile/jordan-rivera/overview"
    - id: profile-name
      action: checkText
      target: profileName
      value: Michael
      gateId: overview-data-card
  assertions:
    - id: assert-name
      kind: visible
      target: profileName
      gateId: overview-data-card
```
""",
        encoding="utf-8",
    )

    result = run_command.run(tmp_path, "profile-view-unauth", core_cmd=str(FAKE_CORE), interactive=False)
    repair = repair_command.run(tmp_path, "profile-view-unauth")

    assert result["coreStatus"] == "passed"
    assert result["coverageStatus"] == "incomplete"
    assert any(item["gateId"] == "projects-tab-content" for item in result["runtimeContradictions"])
    assert repair["repair"]["proposals"]
