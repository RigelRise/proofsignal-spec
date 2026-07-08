from __future__ import annotations

import json
import contextlib
import io
import os
import stat
import sys
from pathlib import Path

from helpers import CliTestCase, FAKE_CORE
from verifysignal_spec.cli import main
from verifysignal_spec.workspace.repository import load_document


class CoreSetupContractTests(CliTestCase):
    def test_core_setup_json_ready_contract(self) -> None:
        code, out, err = self.cli(["core", "setup", "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["schemaVersion"], "verifysignal-spec-core-setup/v1")
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["source"], "env")
        self.assertEqual(payload["coreCommand"], str(FAKE_CORE))
        self.assertTrue(payload["persisted"])
        self.assertFalse(payload["oneTime"])
        self.assertEqual(payload["selectedCandidate"]["status"], "compatible")
        self.assertIn("report.inspect", payload["requiredOperationsByName"])
        self.assertEqual(payload["missingOperations"], [])
        self.assertEqual(payload["incompatibleOperations"], [])

    def test_core_setup_json_missing_contract(self) -> None:
        os.environ["VERIFYSIGNAL_CORE_CMD"] = "missing-verifysignal-core-contract"

        code, out, err = self.cli(["core", "setup", "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["status"], "missing")
        self.assertIsNone(payload.get("selectedCandidate"))
        self.assertEqual(payload["recoveryCommand"], "verifysignal core setup --json")
        self.assertTrue(payload["attempts"])

    def test_core_setup_json_incompatible_contract(self) -> None:
        os.environ["FAKE_VERIFYSIGNAL_MODE"] = "incompatible-run-schema"

        code, out, err = self.cli(["core", "setup", "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["status"], "incompatible")
        self.assertEqual(payload["source"], "env")
        self.assertEqual(payload["incompatibleOperations"][0]["operationName"], "run")
        self.assertEqual(payload["attempts"][0]["terminal"], True)

    def test_core_setup_json_error_contract(self) -> None:
        failing = self.project / "bad-core"
        _write_executable(failing, f"#!{sys.executable}\nimport sys\nsys.exit(9)\n")
        os.environ["VERIFYSIGNAL_CORE_CMD"] = str(failing)

        code, out, err = self.cli(["core", "setup", "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["source"], "env")
        self.assertEqual(payload["recoveryCommand"], "verifysignal core setup --json")

    def test_core_setup_one_time_override_contract(self) -> None:
        code, out, err = self.cli([
            "core",
            "setup",
            "--project",
            str(self.project),
            "--core-cmd",
            str(FAKE_CORE),
            "--no-persist",
            "--json",
        ])

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["source"], "explicit")
        self.assertTrue(payload["oneTime"])
        self.assertFalse(payload["persisted"])
        workspace = load_document(self.project / ".verifysignal/workspace.yaml")
        self.assertNotIn("coreCommand", workspace)


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_core_setup_help_lists_public_options() -> None:
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        try:
            main(["core", "setup", "--help"])
        except SystemExit as exc:
            assert exc.code == 0

    help_text = stdout.getvalue()
    assert "Discover, verify, and persist an existing VerifySignal Core command" in help_text
    assert "--core-cmd" in help_text
    assert "--no-persist" in help_text
    assert "--project" in help_text
    assert "--json" in help_text
