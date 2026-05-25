from __future__ import annotations

import time

from helpers import CliTestCase


class ListUseCasesIntegrationTests(CliTestCase):
    def test_lists_twenty_use_cases_under_target(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex"])
        for index in range(20):
            alias = f"case-{index}"
            self.cli(["author", alias, f"Validate case {index}.", "--project", str(self.project)])
        started = time.monotonic()
        code, out, err = self.cli(["list", "--project", str(self.project), "--json"])
        elapsed = time.monotonic() - started
        self.assertEqual(code, 0, err)
        self.assertLess(elapsed, 5)
        self.assertIn("case-19", out)
