from __future__ import annotations

from helpers import CliTestCase, assert_guardrail_template
from verifysignal_spec.integrations.manifests import save_manifest, sha256_text
from verifysignal_spec.workspace.models import AgentIntegrationState, ManagedFileRecord


class WorkflowAgentInstallationTests(CliTestCase):
    def test_claude_workflow_commands_install(self) -> None:
        code, _, err = self.cli(["init", str(self.project), "--integration", "claude", "--json"])
        self.assertEqual(code, 0, err)
        understand = self.project / ".claude" / "skills" / "verifysignal-understand" / "SKILL.md"
        plan = self.project / ".claude" / "skills" / "verifysignal-plan" / "SKILL.md"
        assert understand.exists()
        assert plan.exists()
        assert_guardrail_template(understand.read_text(encoding="utf-8"), "understand")
        assert_guardrail_template(plan.read_text(encoding="utf-8"), "plan")
        assert (self.project / "CLAUDE.md").read_text(encoding="utf-8").find("/verifysignal-*") >= 0

    def test_claude_upgrade_removes_previous_managed_legacy_skills(self) -> None:
        legacy_path = ".claude/skills/verifysignal-spec-author/SKILL.md"
        legacy = self.project / legacy_path
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy_content = "old generated legacy skill\n"
        legacy.write_text(legacy_content, encoding="utf-8")
        save_manifest(
            self.project,
            AgentIntegrationState(
                key="claude",
                displayName="Claude Code",
                installedAt="2026-06-02T00:00:00Z",
                managedFiles=[ManagedFileRecord(path=legacy_path, sha256=sha256_text(legacy_content), source="claude/verifysignal-spec-author", kind="agent-skill")],
            ),
        )

        code, _, err = self.cli(["init", str(self.project), "--integration", "claude", "--json"])

        self.assertEqual(code, 0, err)
        self.assertFalse(legacy.exists())
