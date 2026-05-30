from __future__ import annotations

from proofsignal_spec.integrations.claude import ClaudeIntegration
from proofsignal_spec.integrations.codex import CodexIntegration


def test_codex_and_claude_generated_guidance_preserves_browser_guardrails(tmp_path) -> None:
    files = {item.path: item.content for item in CodexIntegration().render_files(tmp_path)}
    files.update({item.path: item.content for item in ClaudeIntegration().render_files(tmp_path)})

    for root in [".agents/skills", ".claude/skills"]:
        author = files[f"{root}/proofsignal-spec-author/SKILL.md"]
        validate = files[f"{root}/proofsignal-spec-validate/SKILL.md"]
        repair = files[f"{root}/proofsignal-spec-repair/SKILL.md"]
        assert "Confirm the browser target environment before planning executable artifacts" in author
        assert "runtime readiness verifies target resolution, target reachability, required runtime prerequisites, and Core authoring readiness" in validate
        assert "Safe mechanical selector" in repair
        assert "data, credential, required-gate" in repair
        assert "Never persist credential values" in author
