#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys


def main() -> int:
    args = sys.argv[1:]
    mode = os.environ.get("FAKE_PROOFSIGNAL_MODE", "ok")
    if args[:2] == ["version", "--json"]:
        if mode == "incompatible":
            payload = {
                "schema": "proofsignal.version/v1",
                "schemaVersion": 1,
                "operation": "version",
                "status": "passed",
                "data": {"proofsignalVersion": "0.0.0", "contractVersion": "old", "operations": []},
            }
        else:
            payload = {
                "schema": "proofsignal.version/v1",
                "schemaVersion": 1,
                "operation": "version",
                "status": "passed",
                "data": {
                    "proofsignalVersion": "0.1.0",
                    "contractVersion": "proofsignal-public-cli-json/v1",
                    "operations": [
                        {"name": "version", "schema": "proofsignal.version/v1", "schemaVersion": 1, "status": "stable"},
                        {"name": "authoring-check", "schema": "proofsignal.authoring-check/v1", "schemaVersion": 1, "status": "stable"},
                        {"name": "run", "schema": "proofsignal.run/v1", "schemaVersion": 1, "status": "stable"},
                        {"name": "report.inspect", "schema": "proofsignal.report-inspection/v1", "schemaVersion": 1, "status": "stable"},
                    ],
                },
            }
        print(json.dumps(payload))
        return 0
    if args[:2] == ["authoring-check", "run-request"]:
        status = "blocked" if mode == "blocked" else "passed"
        findings = []
        if status == "blocked":
            findings.append(
                {
                    "severity": "blocking",
                    "code": "unresolved-placeholder-marker",
                    "artifact": args[2],
                    "path": "parameters.baseUrl",
                    "message": "Missing baseUrl.",
                    "suggestedFix": "Declare baseUrl as a runtime input.",
                }
            )
        print(
            json.dumps(
                {
                    "schema": "proofsignal.authoring-check/v1",
                    "schemaVersion": 1,
                    "operation": "authoring-check",
                    "status": status,
                    "data": {
                        "artifacts": [{"kind": "runRequest", "path": args[2], "exists": True}],
                        "summary": {"blockers": len(findings), "warnings": 0},
                        "findings": findings,
                        "requiredRuntimeInputs": [],
                        "credentialGroups": [],
                    },
                }
            )
        )
        return 0
    if args and args[0] == "run":
        print(
            json.dumps(
                {
                    "schema": "proofsignal.run/v1",
                    "schemaVersion": 1,
                    "operation": "run",
                    "status": "failed" if mode == "failed" else "passed",
                    "data": {
                        "runId": "fake-run-1",
                        "reportPath": ".proofsignal/runs/login/fake-run-1/report.json",
                        "evidencePath": ".proofsignal/runs/login/fake-run-1/evidence",
                        "summary": {"title": "Fake run", "status": "failed" if mode == "failed" else "passed"},
                    },
                }
            )
        )
        return 0
    if args[:2] == ["report", "inspect"]:
        print(
            json.dumps(
                {
                    "schema": "proofsignal.report-inspection/v1",
                    "schemaVersion": 1,
                    "operation": "report.inspect",
                    "status": "failed",
                    "data": {
                        "reportPath": args[2],
                        "summary": {"status": "failed", "failedStepId": "submit-login"},
                        "reproductionSteps": ["Navigate to /login", "Submit login"],
                        "observedFailure": "Dashboard did not appear.",
                        "expectedBehavior": "Dashboard appears.",
                        "findings": [{"severity": "error", "artifact": ".proofsignal/skills/login.browser.md", "path": "steps[1]", "message": "Selector did not match."}],
                    },
                }
            )
        )
        return 0
    print(json.dumps({"schema": "proofsignal.error/v1", "schemaVersion": 1, "operation": "unknown", "status": "error"}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
