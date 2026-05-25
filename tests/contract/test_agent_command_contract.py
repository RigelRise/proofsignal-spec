from __future__ import annotations

from proofsignal_spec.integrations.claude import ClaudeIntegration
from proofsignal_spec.integrations.codex import CodexIntegration


def test_codex_renders_proofsignal_workflow_skills(tmp_path) -> None:
    files = {item.path: item.content for item in CodexIntegration().render_files(tmp_path)}
    assert ".agents/skills/proofsignal-understand/SKILL.md" in files
    assert ".agents/skills/proofsignal-run/SKILL.md" in files
    assert "proofsignal.understand" in files[".agents/skills/proofsignal-understand/SKILL.md"]
    assert "proofsignal-spec-author" in files[".agents/skills/proofsignal-spec-author/SKILL.md"]


def test_claude_renders_argument_hints_for_workflow_skills(tmp_path) -> None:
    files = {item.path: item.content for item in ClaudeIntegration().render_files(tmp_path)}
    content = files[".claude/skills/proofsignal-specify/SKILL.md"]
    assert "argument-hint:" in content
    assert "<alias>" in content
    assert "<behavior>" in content
    assert "Invoke this command as `/proofsignal-specify`" in content
