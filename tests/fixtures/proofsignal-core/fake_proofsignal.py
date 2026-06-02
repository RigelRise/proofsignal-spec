#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys


def main() -> int:
    args = sys.argv[1:]
    mode = os.environ.get("FAKE_PROOFSIGNAL_MODE", "ok").replace("_", "-")
    protected = bool(args[:2] == ["authoring-check", "run-request"] or (args and args[0] == "run") or args[:2] == ["report", "inspect"])
    if protected and mode in {"requires-entitlement", "rejects-entitlement", "expired-entitlement", "malformed-entitlement"}:
        receipt_path = os.environ.get("PROOFSIGNAL_ENTITLEMENT_RECEIPT")
        error_code = None
        if not receipt_path:
            error_code = "entitlement.missing"
        elif mode == "rejects-entitlement":
            error_code = "entitlement.policy-denied"
        elif mode == "expired-entitlement":
            error_code = "entitlement.expired"
        elif mode == "malformed-entitlement":
            error_code = "entitlement.malformed"
        if error_code:
            print(
                json.dumps(
                    {
                        "schema": "proofsignal.error/v1",
                        "schemaVersion": 1,
                        "operation": args[0] if args else "unknown",
                        "status": "blocked",
                        "data": {
                            "findings": [
                                {
                                    "severity": "blocking",
                                    "code": error_code,
                                    "message": "Entitlement receipt was rejected by Core.",
                                }
                            ]
                        },
                    }
                )
            )
            return 2
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
            operations = [
                {"name": "version", "schema": "proofsignal.version/v1", "schemaVersion": 1, "status": "stable"},
                {"name": "authoring-check", "schema": "proofsignal.authoring-check/v1", "schemaVersion": 1, "status": "stable"},
                {"name": "run", "schema": "proofsignal.run/v1", "schemaVersion": 1, "status": "stable"},
                {"name": "report.inspect", "schema": "proofsignal.report-inspection/v1", "schemaVersion": 1, "status": "stable"},
            ]
            if mode == "missing-report-inspect":
                operations = [operation for operation in operations if operation["name"] != "report.inspect"]
            if mode == "incompatible-run-schema":
                for operation in operations:
                    if operation["name"] == "run":
                        operation["schema"] = "proofsignal.run/v2"
                        operation["schemaVersion"] = 2
            payload = {
                "schema": "proofsignal.version/v1",
                "schemaVersion": 1,
                "operation": "version",
                "status": "passed",
                "data": {
                    "proofsignalVersion": "0.1.0",
                    "contractVersion": "proofsignal-public-cli-json/v1",
                    "operations": operations,
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
        headed = "--headed" in args
        slow_mo = 0
        skill_args = [args[index + 1] for index, item in enumerate(args) if item == "--skill" and index + 1 < len(args)]
        executed_skill = skill_args[0] if skill_args else None
        gate_evidence = []
        if mode == "helper-only":
            executed_skill = "skill.discover-profile"
        elif mode == "full-coverage":
            executed_skill = skill_args[0] if skill_args else "skill.validate-profile-view-unauth-flow"
            gate_evidence = [
                {"id": "profile-name", "source": "assertion", "gateId": "overview-data-card", "status": "passed", "target": "profileName"},
                {"id": "project-card", "source": "assertion", "gateId": "projects-tab-content", "status": "passed", "target": "projectCard"},
                {
                    "id": "profile-query",
                    "source": "network",
                    "gateId": "overview-profile-query",
                    "status": "passed",
                    "method": "POST",
                    "urlContains": "graphql",
                    "expectedStatus": 200,
                    "publicMatchKeys": ["urlContains"],
                },
            ]
        elif mode in {"failed-with-partial", "aborted-activity-wait"}:
            gate_evidence = [{"id": "profile-name", "source": "assertion", "gateId": "overview-data-card", "status": "passed", "target": "profileName"}]
        if "--slow-mo" in args:
            try:
                slow_mo = int(args[args.index("--slow-mo") + 1])
            except Exception:
                slow_mo = -1
        print(
            json.dumps(
                {
                    "schema": "proofsignal.run/v1",
                    "schemaVersion": 1,
                    "operation": "run",
                    "status": "failed" if mode in {"failed", "failed-with-partial", "aborted-activity-wait"} else "passed",
                    "data": {
                        "runId": "fake-run-1",
                        "reportPath": ".proofsignal/runs/login/fake-run-1/report.json",
                        "evidencePath": ".proofsignal/runs/login/fake-run-1/evidence",
                        "summary": {
                            "title": "Fake run",
                            "status": "failed" if mode in {"failed", "failed-with-partial", "aborted-activity-wait"} else "passed",
                            "failedStepId": "scroll-to-activity" if mode == "aborted-activity-wait" else None,
                            "error": "Timeout waiting for .chakra-container .swiper-slide while activity skeletons were visible."
                            if mode == "aborted-activity-wait"
                            else None,
                        },
                        "args": args,
                        "headed": headed,
                        "slowMoMs": slow_mo,
                        "executedSkill": executed_skill,
                        "gateEvidence": gate_evidence,
                    },
                }
            )
        )
        return 0
    if args[:2] == ["report", "inspect"]:
        if mode == "report-main-skill":
            finding = {
                "severity": "error",
                "artifact": ".proofsignal/run-requests/login.yaml",
                "path": "skills",
                "code": "main-skill-ordering",
                "message": "Helper skill executed before main skill.",
            }
        elif mode == "aborted-activity-wait":
            finding = {
                "severity": "error",
                "artifact": ".proofsignal/skills/validate-home-page-unauth-flow.browser.md",
                "path": "steps.scroll-to-activity",
                "code": "wait-timeout",
                "message": "Step scroll-to-activity timed out waiting for .chakra-container .swiper-slide while activity skeletons were visible.",
                "failedStepId": "scroll-to-activity",
                "gateId": "home-activity-slider",
            }
        else:
            finding = {
                "severity": "error",
                "artifact": ".proofsignal/skills/login.browser.md",
                "path": "steps[1]",
                "message": "Selector did not match.",
            }
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
                        "findings": [finding],
                    },
                }
            )
        )
        return 0
    print(json.dumps({"schema": "proofsignal.error/v1", "schemaVersion": 1, "operation": "unknown", "status": "error"}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
