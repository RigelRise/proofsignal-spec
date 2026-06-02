from __future__ import annotations

import json
import os

from helpers import CliTestCase

from tests.fixtures.workflows.guardrails import create_ready_use_case_workspace, create_registry_missing_record_path
from tests.fixtures.workflows.main_skill_run_coverage import create_main_skill_coverage_workspace
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
        self.assertEqual(result["coreReadiness"]["contractVersion"], "proofsignal-public-cli-json/v1")
        self.assertIn("report.inspect", result["coreReadiness"]["requiredOperationsByName"])
        self.assertIn("complete ProofSignal validation and browser execution experience", result["coreReadiness"]["message"])
        blocker = next(item for item in result["blockers"] if item["code"] == "core.missing")
        self.assertEqual(blocker["category"], "environment")
        self.assertEqual(blocker["recoveryCommand"], "proofsignal core setup --json")
        self.assertFalse(blocker["repairable"])

    def test_core_compatibility_fields_are_reported_when_core_is_available(self) -> None:
        create_ready_use_case_workspace(self.project, "login")
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
        self.assertEqual(code, 0, err)
        result = json.loads(out)
        self.assertEqual(result["coreReadiness"]["status"], "available")
        self.assertEqual(result["coreReadiness"]["contractVersion"], "proofsignal-public-cli-json/v1")
        self.assertEqual(result["coreReadiness"]["missingOperations"], [])
        self.assertEqual(result["coreReadiness"]["requiredOperationsByName"]["authoring-check"]["schemaName"], "proofsignal.authoring-check/v1")

    def test_core_incompatible_schema_reports_public_operation_details(self) -> None:
        create_ready_use_case_workspace(self.project, "login")
        os.environ["FAKE_PROOFSIGNAL_MODE"] = "incompatible-run-schema"

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
        self.assertEqual(result["coreReadiness"]["status"], "incompatible")
        self.assertEqual(result["coreReadiness"]["incompatibleOperations"][0]["operationName"], "run")
        self.assertEqual(result["coreReadiness"]["incompatibleOperations"][0]["actualSchema"], "proofsignal.run/v2")
        self.assertIn("Upgrade ProofSignal Core", result["coreReadiness"]["recoveryAction"])

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

    def test_validate_output_describes_authored_evidence_not_executed_browser_flow(self) -> None:
        create_main_skill_coverage_workspace(self.project)

        code, out, err = self.cli([
            "validate",
            "profile-view-unauth",
            "--project",
            str(self.project),
            "--runtime-readiness",
            "--json",
        ])

        self.assertEqual(code, 0, err)
        result = json.loads(out)
        self.assertEqual(result["authoredEvidenceCoverageStatus"], "complete")
        self.assertEqual(result["runtimeReadinessStatus"], "passed")
        self.assertFalse(result["fullBrowserFlowExecuted"])
        self.assertIn("mapped authored evidence", result["readinessSummary"])
        self.assertIn("full browser flow has not executed", result["readinessSummary"])
