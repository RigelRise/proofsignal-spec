from __future__ import annotations

from helpers import CliTestCase


class IntegrationPortabilityTests(CliTestCase):
    def test_switching_agents_preserves_use_cases(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex"])
        self.cli(["author", "login", "Validate login.", "--project", str(self.project)])
        self.cli(["integration", "install", "claude", "--project", str(self.project)])
        self.cli(["integration", "use", "claude", "--project", str(self.project)])
        code, out, err = self.cli(["list", "--project", str(self.project), "--json"])
        self.assertEqual(code, 0, err)
        self.assertIn("login", out)
