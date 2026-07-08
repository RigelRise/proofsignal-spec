from __future__ import annotations

import json

from helpers import CliTestCase

from verifysignal_spec.workspace.repository import load_document, save_document
from tests.fixtures.workflows.guardrails import create_ready_use_case_workspace


class WorkflowStructuralValidationIntegrationTests(CliTestCase):
    def test_validate_command_returns_readiness_result_without_core(self) -> None:
        create_ready_use_case_workspace(self.project, "login")
        workspace_path = self.project / ".verifysignal/workspace.yaml"
        workspace = load_document(workspace_path)
        workspace["coreCommand"] = "missing-verifysignal-core-for-test"
        save_document(workspace_path, workspace)

        code, out, err = self.cli(["validate", "login", "--project", str(self.project), "--json"])
        self.assertEqual(code, 2, err)
        result = json.loads(out)
        self.assertEqual(result["schemaVersion"], "verifysignal-spec-validation-readiness/v1")
        self.assertEqual(result["structuralValidation"]["status"], "pass")
        self.assertEqual(result["coreReadiness"]["status"], "missing")
