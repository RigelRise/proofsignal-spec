from __future__ import annotations

import json

from helpers import CliTestCase


class WorkflowCliContractTests(CliTestCase):
    def test_workflow_info_json_contract(self) -> None:
        code, out, err = self.cli(["workflow", "info", "verifysignal-use-case", "--project", str(self.project), "--json"])
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["schemaVersion"], "verifysignal-spec-workflow-info/v1")
        self.assertEqual(payload["nativeCommands"]["understand"], "/verifysignal-understand")

    def test_workflow_run_status_and_resume_contract(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex", "--json"])
        code, out, err = self.cli([
            "workflow",
            "run",
            "verifysignal-use-case",
            "--goal",
            "Validate login.",
            "--alias",
            "login",
            "--project",
            str(self.project),
            "--json",
        ])
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["schemaVersion"], "verifysignal-spec-workflow-run/v1")
        self.assertEqual(payload["nextCommand"], "/verifysignal-understand login")

        code, out, err = self.cli(["workflow", "status", payload["runId"], "--project", str(self.project), "--json"])
        self.assertEqual(code, 0, err)
        status = json.loads(out)
        self.assertEqual(status["runId"], payload["runId"])

    def test_workflow_validate_contract_uses_existing_core_adapter(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex", "--json"])
        self.cli(["author", "login", "Validate login.", "--project", str(self.project), "--json"])
        code, out, err = self.cli(["validate", "login", "--project", str(self.project), "--json"])
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertIn("core", payload)
