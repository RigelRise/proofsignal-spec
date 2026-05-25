from __future__ import annotations

import time

from helpers import CliTestCase


class InitCodexIntegrationTests(CliTestCase):
    def test_fresh_init_completes_quickly_and_installs_codex(self) -> None:
        started = time.monotonic()
        code, _, err = self.cli(["init", str(self.project), "--integration", "codex", "--json"])
        elapsed = time.monotonic() - started
        self.assertEqual(code, 0, err)
        self.assertLess(elapsed, 300)
        self.assertTrue((self.project / ".proofsignal" / "workspace.yaml").exists())
        self.assertTrue((self.project / "AGENTS.md").exists())
