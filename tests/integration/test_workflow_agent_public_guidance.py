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
