from __future__ import annotations

from helpers import CliTestCase


class RepairFromReportTests(CliTestCase):
    def test_report_inspection_repair_can_be_approved(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex"])
        self.cli(["author", "login", "Validate login.", "--project", str(self.project)])
        report = self.project / "report.json"
        report.write_text("{}", encoding="utf-8")
        code, out, err = self.cli(["repair", "login", "--project", str(self.project), "--from-report", str(report), "--approve", "--json"])
        self.assertEqual(code, 0, err)
        self.assertIn("applied", out)
