from __future__ import annotations

from helpers import CliTestCase, assert_guardrail_template


class WorkflowAgentInstallationTests(CliTestCase):
    def test_claude_workflow_commands_install(self) -> None:
        code, _, err = self.cli(["init", str(self.project), "--integration", "claude", "--json"])
        self.assertEqual(code, 0, err)
        understand = self.project / ".claude" / "skills" / "proofsignal-understand" / "SKILL.md"
        plan = self.project / ".claude" / "skills" / "proofsignal-plan" / "SKILL.md"
        assert understand.exists()
        assert plan.exists()
        assert_guardrail_template(understand.read_text(encoding="utf-8"), "understand")
        assert_guardrail_template(plan.read_text(encoding="utf-8"), "plan")
        assert (self.project / "CLAUDE.md").read_text(encoding="utf-8").find("/proofsignal-*") >= 0
