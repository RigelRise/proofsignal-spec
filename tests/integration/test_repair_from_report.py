from __future__ import annotations

import os

from helpers import CliTestCase


class RepairFromReportTests(CliTestCase):
    def test_deterministic_report_inspection_repair_can_be_approved(self) -> None:
        os.environ["FAKE_PROOFSIGNAL_MODE"] = "report-main-skill"
        self.cli(["init", str(self.project), "--integration", "codex"])
        self.cli(["author", "login", "Validate login.", "--project", str(self.project)])
        report = self.project / "report.json"
        report.write_text("{}", encoding="utf-8")
        code, out, err = self.cli(["repair", "login", "--project", str(self.project), "--from-report", str(report), "--approve", "--json"])
        self.assertEqual(code, 0, err)
        self.assertIn("applied", out)
        self.assertIn("readyForRun", out)

    def test_report_selector_repair_requires_confirmation_before_revalidation(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex"])
        self.cli(["author", "login", "Validate login.", "--project", str(self.project)])
        report = self.project / "report.json"
        report.write_text("{}", encoding="utf-8")

        code, out, err = self.cli(["repair", "login", "--project", str(self.project), "--from-report", str(report), "--approve", "--json"])

        self.assertEqual(code, 0, err)
        repair = __import__("json").loads(out)["repair"]
        self.assertEqual(repair["approvalStatus"], "conflict")
        self.assertFalse(repair["readyForRun"])
        self.assertEqual(repair["revalidation"]["status"], "not-run")
        self.assertTrue(any(item.get("safeCategory") == "selector-ambiguity" for item in repair["recommendations"]))
        self.assertTrue(all(item.get("requiresUserDecision") for item in repair["recommendations"]))

    def test_safe_repair_matrix_covers_supported_categories(self) -> None:
        from proofsignal_spec.workflows.repair_recommendations import classify_repair_findings

        findings = [
            {"code": "strict-mode-violation", "message": "locator matched multiple elements"},
            {"code": "wait-timeout", "message": "network wait timed out"},
            {"code": "main-skill-ordering", "message": "executed helper before main"},
            {"code": "debug-slowmo-default", "message": "slowMoMs is 0 in debug"},
            {"code": "missing-gateid", "message": "gateId is absent"},
        ]

        recommendations = classify_repair_findings(findings)

        assert {item.safeCategory for item in recommendations} == {
            "selector-ambiguity",
            "wait-strategy",
            "main-skill-ordering",
            "run-profile-defaults",
            "gateid-mapping",
        }
        assert {
            item.safeCategory
            for item in recommendations
            if item.requiresUserDecision
        } == {"selector-ambiguity", "wait-strategy", "gateid-mapping"}

    def test_activity_skeleton_report_recommends_wait_flow_fix(self) -> None:
        os.environ["FAKE_PROOFSIGNAL_MODE"] = "aborted-activity-wait"
        self.cli(["init", str(self.project), "--integration", "codex"])
        self.cli(["author", "home-page-unauth", "Validate home page.", "--project", str(self.project)])
        report = self.project / "report.json"
        report.write_text("{}", encoding="utf-8")

        code, out, err = self.cli(["repair", "home-page-unauth", "--project", str(self.project), "--from-report", str(report), "--json"])

        self.assertEqual(code, 4, err)
        recommendations = __import__("json").loads(out)["repair"]["recommendations"]
        self.assertEqual(recommendations[0]["runtimeCategory"], "wait-flow-issue")
        self.assertEqual(recommendations[0]["safeCategory"], "wait-strategy")
        self.assertTrue(recommendations[0]["requiresUserDecision"])
        self.assertNotIn("mark conditional", str(recommendations).lower())
