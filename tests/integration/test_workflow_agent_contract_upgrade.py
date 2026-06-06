from __future__ import annotations

from proofsignal_spec.integrations.claude import ClaudeIntegration
from proofsignal_spec.integrations.codex import CodexIntegration


def test_regenerated_agent_guidance_contains_public_contract_upgrade_instructions(tmp_path) -> None:
    codex_files = {item.path: item.content for item in CodexIntegration().render_files(tmp_path)}
    claude_files = {item.path: item.content for item in ClaudeIntegration().render_files(tmp_path)}

    for files, root in [(codex_files, ".agents/skills"), (claude_files, ".claude/skills")]:
        implement = files[f"{root}/proofsignal-implement/SKILL.md"]
        assert "stagePayloadContracts" in implement
        assert "coreExecutableContract" in implement
        assert "browserAuthoringContract" in implement
        assert "non-authoritative examples" in implement
        assert "Regenerate the agent integration" in implement
