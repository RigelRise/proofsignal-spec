from __future__ import annotations

from verifysignal_spec.integrations.codex import CodexIntegration


def test_installed_templates_stop_on_unsupported_workflow_contract(tmp_path) -> None:
    files = {item.path: item.content for item in CodexIntegration().render_files(tmp_path)}
    for stage in ["understand", "specify"]:
        content = files[f".agents/skills/verifysignal-{stage}/SKILL.md"]
        assert "workflow.guardrails/v1" in content
        assert "stop immediately" in content
        assert "upgrade `verifysignal` and regenerate the agent integration" in content
        assert "Do not use `npx` or package-runner wrappers" in content
    assert "Do not inspect the repository" in files[".agents/skills/verifysignal-understand/SKILL.md"]
    assert "Do not fall back to `verifysignal check`, directory listing, repository inspection, or use-case questions" in files[".agents/skills/verifysignal-specify/SKILL.md"]
