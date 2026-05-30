from __future__ import annotations

from helpers import assert_public_workflow_contract_guidance
from proofsignal_spec.integrations.claude import ClaudeIntegration
from proofsignal_spec.integrations.codex import CodexIntegration


def test_codex_and_claude_guidance_forbid_package_internal_schema_discovery(tmp_path) -> None:
    files = {item.path: item.content for item in CodexIntegration().render_files(tmp_path)}
    files.update({item.path: item.content for item in ClaudeIntegration().render_files(tmp_path)})

    for path, content in files.items():
        if "proofsignal-" not in path:
            continue
        if any(stage in path for stage in ["specify", "clarify", "plan", "tasks", "implement"]):
            assert_public_workflow_contract_guidance(content)
            assert "Do not inspect installed package source" in content


def test_codex_and_claude_guidance_describes_first_run_stage_cards(tmp_path) -> None:
    files = {item.path: item.content for item in CodexIntegration().render_files(tmp_path)}
    files.update({item.path: item.content for item in ClaudeIntegration().render_files(tmp_path)})

    relevant = "\n".join(content for path, content in files.items() if "proofsignal-run" in path or "proofsignal-spec-run" in path or path in {"AGENTS.md", "CLAUDE.md"})

    assert "stage card" in relevant.lower()
    assert "status marker" in relevant.lower()
    assert "why it matters" in relevant.lower()
    assert "primary evidence" in relevant.lower()
    assert "next action" in relevant.lower()
