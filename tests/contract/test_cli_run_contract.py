from __future__ import annotations

import json

from helpers import CliTestCase


class RunContractTests(CliTestCase):
    def test_run_json_preserves_core_status(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex"])
        self.cli(["author", "login", "Validate login.", "--project", str(self.project)])
        code, out, err = self.cli(["run", "login", "--project", str(self.project), "--json", "--non-interactive"])
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(payload["reportPath"], ".proofsignal/runs/login/fake-run-1/report.json")
