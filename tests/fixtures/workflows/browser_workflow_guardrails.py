from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.workspace.models import ArtifactReference, RuntimeInputRequirement, UseCaseRecord
from proofsignal_spec.workspace.repository import init_workspace, save_use_case
from proofsignal_spec.workflows.models import BrowserTargetEnvironment, RuntimePrerequisite, RuntimeReadinessCheck


ALIAS = "browser-target-guardrail"
TARGET_URL = "https://app.example.test"


def target_environment(url: str = TARGET_URL) -> BrowserTargetEnvironment:
    return BrowserTargetEnvironment(kind="staging-url", locator=url, sourceStage="clarify", resolutionStatus="resolved")


def runtime_prerequisite(name: str = "baseUrl", *, status: str = "passed") -> RuntimePrerequisite:
    return RuntimePrerequisite(
        id=name,
        type="target-environment",
        status="resolved" if status == "passed" else "unresolved",
        valueRef="workflow.stageHandoffDecisions.browserTargetEnvironment",
        sourceStage="clarify",
    )


def runtime_readiness_check(status: str = "passed", url: str = TARGET_URL) -> RuntimeReadinessCheck:
    target = target_environment(url)
    return RuntimeReadinessCheck(
        useCaseAlias=ALIAS,
        status=status,
        targetResolutionStatus="resolved",
        targetReachabilityStatus="reachable",
        requiredPrerequisiteStatus="complete",
        authoringReadinessStatus="passed",
        fullBrowserFlowExecuted=False,
        targetLocator=target.locator,
        findingIds=[],
        message="Runtime readiness passed without executing the full browser flow.",
    )


def create_browser_target_workspace(project: Path, *, target_url: str = TARGET_URL) -> Path:
    init_workspace(project)
    workflow = {
        "stageHandoffDecisions": [
            {
                "key": "browserTargetEnvironment",
                "status": "active",
                "sourceStage": "clarify",
                "valueSummary": target_url,
                "appliesTo": ALIAS,
            }
        ]
    }
    record = UseCaseRecord(
        alias=ALIAS,
        title="Browser Target Guardrail",
        description="Validate browser target handoff guardrails.",
        runRequest=ArtifactReference(path=f".proofsignal/run-requests/{ALIAS}.yaml", kind="run-request"),
        mainSkill=ArtifactReference(path=".proofsignal/skills/browser-target.browser.md", kind="skill"),
        runtimeInputs=[
            RuntimeInputRequirement(
                name="baseUrl",
                required=True,
                description="Base URL of the target browser application.",
                persistValue=False,
            )
        ],
        workflow=workflow,
    )
    save_use_case(project, record)
    return project


def guarded_run_request(target_url: str = TARGET_URL) -> dict[str, Any]:
    return {
        "schemaVersion": "qa-run-request/v1",
        "request": {"id": f"request.{ALIAS}", "name": "Browser Target Guardrail"},
        "target": "browser",
        "parameters": {"baseUrl": target_url},
        "skills": [{"id": "skill.browser-target", "version": "1.0.0"}],
    }
