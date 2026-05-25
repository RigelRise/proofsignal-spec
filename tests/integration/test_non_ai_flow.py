from __future__ import annotations

from helpers import CliTestCase


class NonAiFlowTests(CliTestCase):
    def test_list_and_run_work_after_integration_removed(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex"])
        self.cli(["author", "login", "Validate login.", "--project", str(self.project)])
        self.cli(["integration", "remove", "codex", "--project", str(self.project), "--force"])
        self.assertEqual(self.cli(["list", "--project", str(self.project)])[0], 0)
        self.assertEqual(self.cli(["run", "login", "--project", str(self.project), "--non-interactive"])[0], 0)
