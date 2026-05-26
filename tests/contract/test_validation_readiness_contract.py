from __future__ import annotations

import json

from helpers import CliTestCase

from tests.fixtures.workflows.guardrails import create_ready_use_case_workspace, create_registry_missing_record_path
from proofsignal_spec.workspace.repository import load_document, save_document


class ValidationReadinessContractTests(CliTestCase):
    def test_structural_validation_runs_when_core_is_missing(self) -> None:
        create_ready_use_case_workspace(self.project, "login")
        workspace_path = self.project / ".proofsignal/workspace.yaml"
        workspace = load_document(workspace_path)
        workspace["coreCommand"] = "missing-proofsignal-core-for-test"
        save_document(workspace_path, workspace)
        code, out, err = self.cli([
            "workflow",
            "check",
            "validate",
            "--alias",
            "login",
            "--project",
            str(self.project),
            "--json",
        ])
        self.assertEqual(code, 2, err)
        result = json.loads(out)
        self.assertEqual(result["schemaVersion"], "proofsignal-spec-validation-readiness/v1")
        self.assertEqual(result["structuralValidation"]["status"], "pass")
        self.assertEqual(result["coreReadiness"]["status"], "missing")
        self.assertIn("complete ProofSignal validation and browser execution experience", result["coreReadiness"]["message"])

    def test_malformed_registry_returns_migration_plan(self) -> None:
        create_registry_missing_record_path(self.project, "login")
        code, out, err = self.cli([
            "workflow",
            "check",
            "validate",
            "--alias",
            "login",
            "--project",
            str(self.project),
            "--json",
        ])
        self.assertEqual(code, 2, err)
        result = json.loads(out)
        self.assertEqual(result["status"], "blocked")
        plans = result["structuralValidation"]["migrationPlans"]
        self.assertEqual(plans[0]["id"], "migrate-registry-record-path-login")

    def test_migration_requires_current_approved_plan(self) -> None:
        create_registry_missing_record_path(self.project, "login")
        code, out, err = self.cli([
            "workflow",
            "migrate",
            "--approve",
            "migrate-registry-record-path-login",
            "--project",
            str(self.project),
            "--json",
        ])
        self.assertEqual(code, 0, err)
        result = json.loads(out)
        self.assertEqual(result["schemaVersion"], "proofsignal-spec-workflow-migration-result/v1")
        self.assertEqual(result["status"], "applied")

        code, out, err = self.cli([
            "workflow",
            "migrate",
            "--approve",
            "migrate-registry-record-path-login",
            "--project",
            str(self.project),
            "--json",
        ])
        self.assertEqual(code, 2, err)
        self.assertEqual(json.loads(out)["status"], "blocked")
