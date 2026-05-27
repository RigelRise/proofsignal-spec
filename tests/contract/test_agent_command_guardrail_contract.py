from __future__ import annotations

from helpers import agent_template, assert_guardrail_template


def test_all_agent_command_templates_include_guardrail_contract() -> None:
    for stage in ["understand", "specify", "clarify", "plan", "tasks", "implement", "validate", "list", "run", "repair"]:
        assert_guardrail_template(agent_template(stage), stage)


def test_validate_template_mentions_structural_validation_and_core_requirement() -> None:
    content = agent_template("validate")
    assert "structuralValidation" in content
    assert "ProofSignal Core is required for the complete ProofSignal validation and browser execution experience" in content
    assert "proofsignal-spec workflow migrate --approve <migration-id> --json" in content


def test_implement_template_uses_canonical_skill_shape_and_cli_persistence() -> None:
    content = agent_template("implement")
    assert ".proofsignal/skills/<name>.browser.md" in content
    assert "proofsignal-spec workflow persist implement" in content
    assert "never manually author registry entries" in content
    assert "Do not use `proofsignal-spec author`" in content
    assert "the CLI owns the final `qa-run-request/v1` and `qa-skill/v1` envelopes" in content
    assert "intent.browser.steps" in content
    assert "browserAuthoringContract" in content
    assert "`navigate` uses `value`" in content
    assert "intent.browser.targets" in content


def test_plan_template_makes_main_skill_executable() -> None:
    content = agent_template("plan")
    assert "Make the main skill executable by Core for the complete planned validation path" in content
    assert "workflow show --alias <alias> --json" in content


def test_run_template_forbids_summarizing_incomplete_runs_as_passed() -> None:
    content = agent_template("run")
    assert "Core `passed` result can still be `coverageStatus: incomplete`" in content
    assert "Do not summarize `status: incomplete` as passed" in content
