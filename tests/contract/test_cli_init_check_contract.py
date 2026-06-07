from __future__ import annotations

import json

from helpers import CliTestCase, FAKE_CORE
from proofsignal_spec.workspace.repository import load_document


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

    def test_check_core_cmd_override_does_not_persist_to_workspace(self) -> None:
        code, _out, err = self.cli(["init", str(self.project), "--integration", "codex", "--core-cmd", str(FAKE_CORE), "--json"])
        self.assertEqual(code, 0, err)

        code, out, _err = self.cli(["check", "--project", str(self.project), "--core-cmd", "missing-proofsignal-core-for-check", "--json"])

        self.assertEqual(code, 2)
        payload = json.loads(out)
        workspace = load_document(self.project / ".proofsignal" / "workspace.yaml")
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["managedRuntimeReadiness"]["runtimeCommand"], "missing-proofsignal-core-for-check")
        self.assertEqual(workspace["coreCommand"], str(FAKE_CORE))
