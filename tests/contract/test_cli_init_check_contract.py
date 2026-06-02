from __future__ import annotations

import json

from helpers import CliTestCase


class InitCheckContractTests(CliTestCase):
    def test_init_json_contract_and_check(self) -> None:
        code, out, err = self.cli(["init", str(self.project), "--integration", "codex", "--json"])
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["integration"], "codex")
        self.assertTrue((self.project / ".proofsignal").exists())
        self.assertTrue((self.project / ".agents" / "skills" / "proofsignal-specify" / "SKILL.md").exists())
        self.assertFalse((self.project / ".agents" / "skills" / "proofsignal-spec-author" / "SKILL.md").exists())
        self.assertTrue(payload["core"]["compatible"])

        code, out, err = self.cli(["check", "--project", str(self.project), "--json"])
        self.assertEqual(code, 0, err)
        check = json.loads(out)
        self.assertEqual(check["schemaVersion"], "proofsignal-spec-check/v1")
        self.assertEqual(check["status"], "passed")
