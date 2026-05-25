from __future__ import annotations

from helpers import CliTestCase


class WorkflowAgentInstallationTests(CliTestCase):
    def test_claude_workflow_commands_install(self) -> None:
        code, _, err = self.cli(["init", str(self.project), "--integration", "claude", "--json"])
        self.assertEqual(code, 0, err)
        assert (self.project / ".claude" / "skills" / "proofsignal-understand" / "SKILL.md").exists()
        assert (self.project / ".claude" / "skills" / "proofsignal-plan" / "SKILL.md").exists()
        assert (self.project / "CLAUDE.md").read_text(encoding="utf-8").find("/proofsignal-*") >= 0

