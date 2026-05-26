from __future__ import annotations

from proofsignal_spec.integrations.codex import CodexIntegration


def test_installed_templates_stop_on_unsupported_workflow_contract(tmp_path) -> None:
    files = {item.path: item.content for item in CodexIntegration().render_files(tmp_path)}
    for stage in ["understand", "specify"]:
        content = files[f".agents/skills/proofsignal-{stage}/SKILL.md"]
        assert "workflow.guardrails/v1" in content
        assert "stop immediately" in content
        assert "upgrade `proofsignal-spec` and regenerate the agent integration" in content
        assert "Do not use `npx proofsignal-spec`" in content
    assert "Do not inspect the repository" in files[".agents/skills/proofsignal-understand/SKILL.md"]
    assert "Do not fall back to `proofsignal-spec check`, directory listing, repository inspection, or use-case questions" in files[".agents/skills/proofsignal-specify/SKILL.md"]
