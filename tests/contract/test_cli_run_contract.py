from __future__ import annotations

import json
import os

from helpers import CliTestCase
from proofsignal_spec.workspace.models import RuntimeInputRequirement
from proofsignal_spec.workspace.repository import load_use_case, save_use_case
from tests.fixtures.workflows.main_skill_run_coverage import create_main_skill_coverage_workspace


class RunContractTests(CliTestCase):
    def test_run_json_preserves_core_status(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex"])
        self.cli(["author", "login", "Validate login.", "--project", str(self.project)])
        code, out, err = self.cli(["run", "login", "--project", str(self.project), "--json", "--non-interactive"])
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(payload["reportPath"], ".proofsignal/runs/login/fake-run-1/report.json")

    def test_full_required_gate_coverage_is_passed(self) -> None:
        create_main_skill_coverage_workspace(self.project)
        os.environ["FAKE_PROOFSIGNAL_MODE"] = "full-coverage"

        code, out, err = self.cli(["run", "profile-view-unauth", "--project", str(self.project), "--json", "--non-interactive"])

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(payload["coreStatus"], "passed")
        self.assertEqual(payload["coverageStatus"], "complete")
        self.assertEqual(payload["skillSelectionStatus"], "matched")
        self.assertEqual(payload["missingRequiredGates"], [])

    def test_qa_report_step_gate_ids_drive_required_gate_coverage(self) -> None:
        create_main_skill_coverage_workspace(self.project)
        os.environ["FAKE_PROOFSIGNAL_MODE"] = "qa-report-step-coverage"

        code, out, err = self.cli(["run", "profile-view-unauth", "--project", str(self.project), "--json", "--non-interactive"])

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(payload["coreBrowserStatus"], "passed")
        self.assertEqual(payload["specCoverageStatus"], "complete")
        self.assertEqual(payload["missingRequiredGates"], [])
        self.assertIn("assert-overview-data-card", payload["gateCoverage"][0]["uiEvidenceIds"])

    def test_core_failure_produces_failed_use_case_status_with_partial_coverage(self) -> None:
        create_main_skill_coverage_workspace(self.project)
        os.environ["FAKE_PROOFSIGNAL_MODE"] = "failed-with-partial"

        code, out, err = self.cli(["run", "profile-view-unauth", "--project", str(self.project), "--json", "--non-interactive"])

        self.assertNotEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["coreStatus"], "failed")
        self.assertEqual(payload["coverageStatus"], "diagnostic")
        self.assertEqual(payload["coreBrowserStatus"], "failed")
        self.assertEqual(payload["specCoverageStatus"], "diagnostic")
        self.assertTrue(payload["partialCoverage"])

    def test_core_pass_without_public_gate_evidence_keeps_coverage_incomplete(self) -> None:
        create_main_skill_coverage_workspace(self.project)
        os.environ["FAKE_PROOFSIGNAL_MODE"] = "main-no-gate-evidence"

        code, out, err = self.cli(["run", "profile-view-unauth", "--project", str(self.project), "--json", "--non-interactive"])

        self.assertEqual(code, 2, err)
        payload = json.loads(out)
        self.assertEqual(payload["status"], "incomplete")
        self.assertEqual(payload["coreStatus"], "passed")
        self.assertEqual(payload["coverageStatus"], "incomplete")
        self.assertTrue(payload["missingRequiredGates"])

    def test_run_does_not_accept_runtime_input_override_as_cli_flag(self) -> None:
        create_main_skill_coverage_workspace(self.project)
        os.environ["FAKE_PROOFSIGNAL_MODE"] = "full-coverage"
        record = load_use_case(self.project, "profile-view-unauth")
        record.runtimeInputs = [RuntimeInputRequirement(name="baseUrl", description="Base URL", required=True)]
        save_use_case(self.project, record)
        run_request = self.project / ".proofsignal/run-requests/profile-view-unauth.yaml"
        data = json.loads(run_request.read_text(encoding="utf-8"))
        data["parameters"]["baseUrl"] = ""
        run_request.write_text(json.dumps(data), encoding="utf-8")

        with self.assertRaises(SystemExit) as raised:
            self.cli(
                [
                    "run",
                    "profile-view-unauth",
                    "--project",
                    str(self.project),
                    "--baseUrl",
                    "https://app.example.test",
                    "--non-interactive",
                    "--json",
                ]
            )

        self.assertEqual(raised.exception.code, 2)
