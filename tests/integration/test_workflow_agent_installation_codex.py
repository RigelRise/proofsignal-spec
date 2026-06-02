from __future__ import annotations

from helpers import CliTestCase, assert_guardrail_template


class WorkflowCodexInstallationTests(CliTestCase):
    def test_codex_workflow_commands_install(self) -> None:
        code, _, err = self.cli(["init", str(self.project), "--integration", "codex", "--json"])
        self.assertEqual(code, 0, err)
        understand = self.project / ".agents" / "skills" / "proofsignal-understand" / "SKILL.md"
        run = self.project / ".agents" / "skills" / "proofsignal-run" / "SKILL.md"
        assert understand.exists()
        assert run.exists()
        assert_guardrail_template(understand.read_text(encoding="utf-8"), "understand")
        assert_guardrail_template(run.read_text(encoding="utf-8"), "run")
        assert not (self.project / ".agents" / "skills" / "proofsignal-spec-author" / "SKILL.md").exists()
