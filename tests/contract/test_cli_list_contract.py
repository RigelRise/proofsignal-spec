from __future__ import annotations

import json

from helpers import CliTestCase


class ListContractTests(CliTestCase):
    def test_list_json_schema_and_invalid_record_warning(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex"])
        self.cli(["author", "login", "Validate login.", "--project", str(self.project)])
        (self.project / ".verifysignal" / "use-cases" / "login.yaml").unlink()
        code, out, err = self.cli(["list", "--project", str(self.project), "--json"])
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["schemaVersion"], "verifysignal-spec-list/v1")
        self.assertEqual(payload["useCases"][0]["status"], "invalid")
        self.assertTrue(payload["warnings"])
