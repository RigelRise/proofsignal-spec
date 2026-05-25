from __future__ import annotations

from helpers import CliTestCase


class CliSmokeTests(CliTestCase):
    def test_init_author_list_run_repair_smoke(self) -> None:
        self.assertEqual(self.cli(["init", str(self.project), "--integration", "codex"])[0], 0)
        self.assertEqual(self.cli(["author", "login", "Validate login.", "--project", str(self.project)])[0], 0)
        self.assertEqual(self.cli(["list", "--project", str(self.project)])[0], 0)
        self.assertEqual(self.cli(["run", "login", "--project", str(self.project), "--non-interactive"])[0], 0)
        self.assertEqual(self.cli(["repair", "login", "--project", str(self.project)])[0], 4)
