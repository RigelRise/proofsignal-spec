from __future__ import annotations

from helpers import CliTestCase


class RunUseCaseIntegrationTests(CliTestCase):
    def test_run_records_history_without_credentials(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex"])
        self.cli(["author", "login", "Validate login.", "--project", str(self.project)])
        self.assertEqual(self.cli(["run", "login", "--project", str(self.project), "--non-interactive"])[0], 0)
        history = self.project / ".proofsignal" / "runs" / "login" / "fake-run-1.yaml"
        self.assertTrue(history.exists())
        self.assertNotIn("password", history.read_text(encoding="utf-8").lower())
