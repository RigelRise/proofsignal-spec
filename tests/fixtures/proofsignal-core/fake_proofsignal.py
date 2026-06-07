#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


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
        else:
            receipt_key_id = _receipt_key_id(receipt_path)
            if receipt_key_id and not _public_keys_include(receipt_key_id):
                error_code = "entitlement.key-unknown"
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
                {"name": "contracts", "schema": "proofsignal.contracts/v1", "schemaVersion": 1, "status": "stable"},
                {"name": "authoring-check", "schema": "proofsignal.authoring-check/v1", "schemaVersion": 1, "status": "stable"},
                {"name": "run", "schema": "proofsignal.run/v1", "schemaVersion": 1, "status": "stable"},
                {"name": "report.inspect", "schema": "proofsignal.report-inspection/v1", "schemaVersion": 1, "status": "stable"},
            ]
            if mode == "missing-contracts-operation":
                operations = [operation for operation in operations if operation["name"] != "contracts"]
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
    if args[:2] == ["contracts", "--json"]:
        _increment_contract_counter()
        if mode == "contracts-non-json":
            print("not json")
            return 0
        if mode == "contracts-failed":
            print(
                json.dumps(
                    {
                        "schema": "proofsignal.error/v1",
                        "schemaVersion": 1,
                        "operation": "contracts",
                        "status": "blocked",
                        "data": {
                            "findings": [
                                {
                                    "severity": "blocking",
                                    "code": "contracts.unavailable",
                                    "message": "Core public contract is unavailable.",
                                }
                            ]
                        },
                    }
                )
            )
            return 2
        contract = _contracts_payload(mode)
        print(json.dumps(contract))
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
        elif mode == "qa-report-step-coverage":
            executed_skill = skill_args[0] if skill_args else "skill.validate-profile-view-unauth-flow"
            _write_report(
                ".proofsignal/runs/login/fake-run-1/report.json",
                [
                    {"id": "assert-overview-data-card", "status": "passed", "gateId": "overview-data-card", "evidence": []},
                    {"id": "assert-projects-tab-content", "status": "passed", "gateId": "projects-tab-content", "evidence": []},
                    {"id": "assert-overview-profile-query", "status": "passed", "gateId": "overview-profile-query", "evidence": []},
                ],
            )
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


def _receipt_key_id(receipt_path: str | None) -> str | None:
    if not receipt_path:
        return None
    try:
        data = json.loads(open(receipt_path, encoding="utf-8").read())
    except Exception:
        return None
    if isinstance(data, dict) and isinstance(data.get("signature"), dict):
        return data["signature"].get("keyId")
    if isinstance(data, dict) and isinstance(data.get("receipt"), str):
        try:
            envelope = json.loads(data["receipt"])
        except Exception:
            return None
        signature = envelope.get("signature") if isinstance(envelope, dict) else {}
        return signature.get("keyId") if isinstance(signature, dict) else None
    return None


def _write_report(path: str, steps: list[dict[str, object]]) -> None:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "schemaVersion": "qa-report/v1",
                "runId": "fake-run-1",
                "status": "passed",
                "summary": {"status": "passed", "failedStepId": None},
                "failedStep": None,
                "steps": steps,
                "preconditions": [],
                "evidenceLinks": [],
            }
        ),
        encoding="utf-8",
    )


def _contracts_payload(mode: str) -> dict[str, object]:
    operations = [
        {"name": "version", "schema": "proofsignal.version/v1", "schemaVersion": 1, "status": "stable"},
        {"name": "contracts", "schema": "proofsignal.contracts/v1", "schemaVersion": 1, "status": "stable"},
        {"name": "authoring-check", "schema": "proofsignal.authoring-check/v1", "schemaVersion": 1, "status": "stable"},
        {"name": "run", "schema": "proofsignal.run/v1", "schemaVersion": 1, "status": "stable"},
        {"name": "report.inspect", "schema": "proofsignal.report-inspection/v1", "schemaVersion": 1, "status": "stable"},
    ]
    browser_actions = [
        {"name": "navigate", "status": "stable", "requiredFields": ["value"]},
        {"name": "click", "status": "stable", "requiredFields": ["target"]},
        {"name": "fill", "status": "stable", "requiredFields": ["target", "value"]},
        {"name": "select", "status": "stable", "requiredFields": ["target", "value"]},
        {"name": "waitForText", "status": "stable", "requiredFields": ["target", "value"]},
        {"name": "checkText", "status": "stable", "requiredFields": ["target", "value"]},
        {"name": "checkLocation", "status": "stable", "requiredFields": ["value"]},
        {"name": "captureScreenshot", "status": "stable", "requiredFields": []},
        {"name": "scrollIntoView", "status": "stable", "requiredFields": ["target"]},
        {"name": "awaitNetwork", "status": "stable", "requiredFields": ["match"]},
        {"name": "repeatUntil", "status": "stable", "requiredFields": ["until", "do"]},
    ]
    if mode == "contract-drift":
        browser_actions = [item for item in browser_actions if item["name"] != "repeatUntil"]
        browser_actions.append({"name": "press", "status": "stable", "requiredFields": ["target", "value"]})
    if mode == "experimental-contract":
        browser_actions.append({"name": "dragAndDrop", "status": "experimental", "requiredFields": ["target", "value"]})
    data: dict[str, object] = {
        "operations": operations,
        "runRequest": {
            "status": "stable",
            "schemaVersion": "qa-run-request/v1",
            "fields": [
                {"name": "schemaVersion", "status": "stable", "required": True},
                {"name": "request", "status": "stable", "required": True},
                {"name": "target", "status": "stable", "required": True},
                {"name": "credentialRefs", "status": "stable", "required": False},
                {"name": "skills", "status": "stable", "required": True},
            ],
        },
        "skill": {
            "status": "stable",
            "schemaVersion": "proofsignal-browser-skill/v1",
            "fields": [
                {"name": "browser.targets", "status": "stable", "required": True},
                {"name": "browser.steps", "status": "stable", "required": True},
                {"name": "browser.assertions", "status": "stable", "required": False},
            ],
        },
        "browserWorkflow": {
            "actions": browser_actions,
            "assertions": [
                {"name": "text", "status": "stable", "requiredFields": ["target", "expected"]},
                {"name": "location", "status": "stable", "requiredFields": ["expected"]},
                {"name": "visible", "status": "stable", "requiredFields": ["target"]},
                {"name": "hidden", "status": "stable", "requiredFields": ["target"]},
                {"name": "screenshot-required", "status": "stable", "requiredFields": []},
                {"name": "image-diff", "status": "experimental", "requiredFields": ["target"]},
            ],
            "targetSignals": [
                {"name": "testId", "status": "stable"},
                {"name": "label", "status": "stable"},
                {"name": "text", "status": "stable"},
                {"name": "css", "status": "stable"},
                {"name": "semanticLocator", "status": "stable"},
                {"name": "all", "status": "stable", "composition": ["testId", "css"]},
            ],
            "networkMatchKeys": [
                {"name": "urlContains", "status": "stable"},
                {"name": "method", "status": "stable"},
                {"name": "status", "status": "stable"},
                {"name": "requestBodyContains", "status": "stable"},
                {"name": "responseBodyContains", "status": "stable"},
                {"name": "privateHeaderContains", "status": "experimental"},
            ],
            "metadataKeys": [{"name": "operationName", "status": "stable"}, {"name": "expectedStatus", "status": "stable"}],
            "gateEvidenceRules": {
                "gateId": "UI assertions, network waits, and screenshots must declare gateId to count toward planned gate coverage.",
                "renderedResult": "Required page-view gates need a specific target plus expected text/state/count.",
                "network": "awaitNetwork match uses stable public match keys and expected status.",
            },
        },
        "credentials": {
            "sources": [{"name": "environment", "status": "stable"}, {"name": "prompt-cache", "status": "experimental"}],
            "referenceShape": "credentialRefs.<group>.keys.<field>",
        },
        "placeholders": {
            "credentialSyntax": "{{credentials.<group>.<field>}}",
            "supportedNamespaces": [{"name": "parameters", "status": "stable"}, {"name": "credentials", "status": "stable"}],
        },
        "reportCoverage": {
            "schemaVersion": "qa-report/v1",
            "gateIdFields": ["gateId"],
            "stepCollections": ["steps", "preconditions"],
            "evidenceCollections": ["evidence"],
            "statusField": "status",
            "passedStatus": "passed",
        },
        "publicRedactionPolicy": {
            "publicErrorShape": {
                "forbiddenFields": ["rawValue", "rawRequestBody", "rawResponseBody", "receipt", "receiptPayload", "privateKey", "signedUrl", "absolutePath", "rawPayload"],
            },
            "safeEvidenceReferences": {
                "forbiddenFields": ["rawPayload", "absolutePath", "signedUrl", "storageState", "sessionCookies", "tracePayload", "screenshotPayload"],
            },
        },
        "runtimeTrustHandoff": {
            "entitlementReceiptEnv": "PROOFSIGNAL_ENTITLEMENT_RECEIPT",
            "verificationKeysEnv": "PROOFSIGNAL_ENTITLEMENT_PUBLIC_KEYS_JSON",
        },
    }
    if mode == "contracts-missing-browser":
        data.pop("browserWorkflow")
    if mode == "contracts-malformed-browser":
        data["browserWorkflow"] = []
    return {
        "schema": "proofsignal.contracts/v1",
        "schemaVersion": 1,
        "operation": "contracts",
        "status": "passed",
        "data": {"sections": data},
    }


def _increment_contract_counter() -> None:
    path = os.environ.get("FAKE_PROOFSIGNAL_CONTRACT_COUNTER")
    if not path:
        return
    counter_path = Path(path)
    counter_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        value = int(counter_path.read_text(encoding="utf-8").strip() or "0")
    except Exception:
        value = 0
    counter_path.write_text(str(value + 1), encoding="utf-8")


def _public_keys_include(key_id: str) -> bool:
    raw = os.environ.get("PROOFSIGNAL_ENTITLEMENT_PUBLIC_KEYS_JSON")
    if not raw:
        return False
    try:
        data = json.loads(raw)
    except Exception:
        return False
    keys = data.get("keys") if isinstance(data, dict) else data
    if not isinstance(keys, list):
        return False
    return any(isinstance(item, dict) and item.get("keyId") == key_id for item in keys)


if __name__ == "__main__":
    raise SystemExit(main())
