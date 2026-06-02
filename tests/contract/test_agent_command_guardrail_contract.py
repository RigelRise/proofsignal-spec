from __future__ import annotations

from helpers import agent_template, assert_guardrail_template


def test_all_agent_command_templates_include_guardrail_contract() -> None:
    for stage in ["understand", "specify", "clarify", "plan", "tasks", "implement", "validate", "list", "run", "repair"]:
        assert_guardrail_template(agent_template(stage), stage)


def test_validate_template_mentions_structural_validation_and_core_requirement() -> None:
    content = agent_template("validate")
    assert "structuralValidation" in content
    assert "ProofSignal Core is required for the complete ProofSignal validation and browser execution experience" in content
    assert "runtime readiness verifies target resolution, target reachability, required runtime prerequisites, and Core authoring readiness" in content
    assert "proofsignal workflow migrate --approve <migration-id> --json" in content


def test_implement_template_uses_canonical_skill_shape_and_cli_persistence() -> None:
    content = agent_template("implement")
    assert ".proofsignal/skills/<name>.browser.md" in content
    assert "proofsignal workflow persist implement" in content
    assert "never manually author registry entries" in content
    assert "Do not use `proofsignal author`" in content
    assert "the CLI owns the final `qa-run-request/v1` and `qa-skill/v1` envelopes" in content
    assert "intent.browser.steps" in content
    assert "browserAuthoringContract" in content
    assert "`navigate` uses `value`" in content
    assert "intent.browser.targets" in content
    assert "Run `proofsignal validate <alias> --runtime-readiness` before reporting browser artifacts ready" in content


def test_specify_and_plan_templates_require_browser_target_before_executable_planning() -> None:
    specify = agent_template("specify")
    plan = agent_template("plan")
    assert "Browser validation use cases require a resolved target application environment before executable planning" in specify
    assert "Do not leave `baseUrl` or equivalent target parameters empty after the user has supplied a target" in plan


def test_plan_template_makes_main_skill_executable() -> None:
    content = agent_template("plan")
    assert "Make the main skill executable by Core for the complete planned validation path" in content
    assert "workflow show --alias <alias> --json" in content


def test_run_template_forbids_summarizing_incomplete_runs_as_passed() -> None:
    content = agent_template("run")
    assert "Core `passed` result can still be `coverageStatus: incomplete`" in content
    assert "Do not summarize `status: incomplete` as passed" in content
