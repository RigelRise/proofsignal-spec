from __future__ import annotations

from helpers import CliTestCase


class WorkflowCodexInstallationTests(CliTestCase):
    def test_codex_workflow_commands_install(self) -> None:
        code, _, err = self.cli(["init", str(self.project), "--integration", "codex", "--json"])
        self.assertEqual(code, 0, err)
        assert (self.project / ".agents" / "skills" / "proofsignal-understand" / "SKILL.md").exists()
        assert (self.project / ".agents" / "skills" / "proofsignal-run" / "SKILL.md").exists()
        assert (self.project / ".agents" / "skills" / "proofsignal-spec-author" / "SKILL.md").exists()

