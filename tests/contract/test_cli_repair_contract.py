from __future__ import annotations

import json

from helpers import CliTestCase


class RepairContractTests(CliTestCase):
    def test_repair_requires_approval_by_default(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex"])
        self.cli(["author", "login", "Validate login.", "--project", str(self.project)])
        code, out, _ = self.cli(["repair", "login", "--project", str(self.project), "--json"])
        self.assertEqual(code, 4)
        payload = json.loads(out)
        self.assertEqual(payload["repair"]["approvalStatus"], "pending")
