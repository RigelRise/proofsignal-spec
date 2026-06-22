from __future__ import annotations

from proofsignal_spec.integrations.claude import ClaudeIntegration
from proofsignal_spec.integrations.codex import CodexIntegration


def test_guidance_points_at_policy_set_for_policy_only_changes(tmp_path) -> None:
    # The agent must reach for `proofsignal policy set` to change ONLY the side-effect policy,
    # instead of re-authoring the whole implement payload (the ceremony policy set removes).
    claude = {item.path: item.content for item in ClaudeIntegration().render_files(tmp_path)}
    codex = {item.path: item.content for item in CodexIntegration().render_files(tmp_path)}
    assert "proofsignal policy set" in claude["CLAUDE.md"]
    assert "proofsignal policy set" in codex["AGENTS.md"]


def test_codex_renders_proofsignal_workflow_skills(tmp_path) -> None:
    files = {item.path: item.content for item in CodexIntegration().render_files(tmp_path)}
    assert ".agents/skills/proofsignal-understand/SKILL.md" in files
    assert ".agents/skills/proofsignal-run/SKILL.md" in files
    assert "proofsignal.understand" in files[".agents/skills/proofsignal-understand/SKILL.md"]
    assert ".agents/skills/proofsignal-spec-author/SKILL.md" not in files


def test_claude_renders_argument_hints_for_workflow_skills(tmp_path) -> None:
    files = {item.path: item.content for item in ClaudeIntegration().render_files(tmp_path)}
    content = files[".claude/skills/proofsignal-specify/SKILL.md"]
    assert "argument-hint:" in content
    assert "<alias>" in content
    assert "<behavior>" in content
    assert "Invoke this command as `/proofsignal-specify`" in content


def test_codex_and_claude_validation_guidance_share_live_readiness_facts(tmp_path) -> None:
    codex = {item.path: item.content for item in CodexIntegration().render_files(tmp_path)}
    claude = {item.path: item.content for item in ClaudeIntegration().render_files(tmp_path)}

    codex_content = codex[".agents/skills/proofsignal-validate/SKILL.md"]
    claude_content = claude[".claude/skills/proofsignal-validate/SKILL.md"]
    for phrase in [
        "shared CLI JSON",
        "credential readiness hints",
        "structured confirmation",
        "cleanup lifecycle",
        "side-effect envelope",
    ]:
        assert phrase in codex_content
        assert phrase in claude_content
