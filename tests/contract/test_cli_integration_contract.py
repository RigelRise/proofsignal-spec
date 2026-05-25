from __future__ import annotations

import json

from helpers import CliTestCase


class IntegrationContractTests(CliTestCase):
    def test_integration_commands(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex"])
        code, out, err = self.cli(["integration", "install", "claude", "--project", str(self.project), "--json"])
        self.assertEqual(code, 0, err)
        self.assertIn("claude", out)
        code, out, err = self.cli(["integration", "list", "--project", str(self.project), "--json"])
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertIn("codex", payload["installed"])
        self.assertIn("claude", payload["installed"])
        self.assertEqual(self.cli(["integration", "use", "claude", "--project", str(self.project)])[0], 0)
        self.assertEqual(self.cli(["integration", "upgrade", "claude", "--project", str(self.project)])[0], 0)
        self.assertEqual(self.cli(["integration", "remove", "claude", "--project", str(self.project)])[0], 0)
