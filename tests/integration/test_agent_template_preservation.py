from __future__ import annotations

from proofsignal_spec.integrations.claude import ClaudeIntegration
from proofsignal_spec.integrations.codex import CodexIntegration


def test_codex_and_claude_generated_guidance_preserves_browser_guardrails(tmp_path) -> None:
    files = {item.path: item.content for item in CodexIntegration().render_files(tmp_path)}
    files.update({item.path: item.content for item in ClaudeIntegration().render_files(tmp_path)})

    for root in [".agents/skills", ".claude/skills"]:
        implement = files[f"{root}/proofsignal-implement/SKILL.md"]
        validate = files[f"{root}/proofsignal-validate/SKILL.md"]
        repair = files[f"{root}/proofsignal-repair/SKILL.md"]
        assert "Browser validation use cases require a resolved target application environment" in files[f"{root}/proofsignal-specify/SKILL.md"]
        assert "runtime readiness verifies target resolution, target reachability, required runtime prerequisites, and Core authoring readiness" in validate
        assert "Safe mechanical selector" in repair
        assert "Data assumptions, credentials, required gates" in repair
        assert "Never persist credential values" in implement


def test_specify_and_understand_templates_describe_auto_prepare_without_manual_restart() -> None:
    from helpers import agent_template

    specify = agent_template("specify")
    understand = agent_template("understand")

    assert "auto-prepare" in specify.lower()
    assert "resume" in specify.lower()
    assert "proofsignal workflow recommend-first-run --json" in specify
    assert "Do not present candidateUseCases or recommendedCandidate from workflow check as the product-owned first-run recommendation" in specify
    assert "without requiring the user to manually restart" in specify
    assert "trivial public/read-only" in understand.lower()
    assert "before branch-heavy" in understand.lower()
    assert "partial inventory" in understand.lower()
