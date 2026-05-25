from __future__ import annotations

from __future__ import annotations

import time

from helpers import CliTestCase


class ListPerformanceTests(CliTestCase):
    def test_twenty_registered_use_cases_list_under_five_seconds(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex"])
        for index in range(20):
            self.cli(["author", f"perf-{index}", f"Validate perf {index}.", "--project", str(self.project)])
        started = time.monotonic()
        code, _, err = self.cli(["list", "--project", str(self.project), "--json"])
        self.assertEqual(code, 0, err)
        self.assertLess(time.monotonic() - started, 5)
