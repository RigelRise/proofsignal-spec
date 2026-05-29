from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.workspace.models import ArtifactReference, RunProfile, RuntimeInputRequirement, UseCaseRecord
from proofsignal_spec.workspace.repository import init_workspace, save_document, save_use_case


ALIAS = "home-page-unauth"
BASE_URL = "https://app.example.test"


def minimal_specify_payload(alias: str = ALIAS, *, target: str = BASE_URL) -> dict[str, Any]:
    return {
        "alias": alias,
        "surface": "/",
        "behavior": "Validate the public home page for an unauthenticated visitor.",
        "expectedOutcome": "Hero, activity slider, Teams table, and Brands tab render populated content.",
        "customSourceReason": "Workflow dogfood fixture.",
        "targetEnvironment": {"kind": "staging-url", "locator": target},
    }


def malformed_specify_payload(alias: str = ALIAS) -> dict[str, Any]:
    payload = minimal_specify_payload(alias)
    payload.pop("expectedOutcome")
    return payload


def browser_artifact_plan() -> dict[str, Any]:
    return {
        "runRequest": f".proofsignal/run-requests/{ALIAS}.yaml",
        "mainSkill": f".proofsignal/skills/validate-{ALIAS}-flow.browser.md",
        "reusableSkills": [f".proofsignal/skills/validate-{ALIAS}-flow.browser.md"],
        "runtimeInputs": [{"name": "baseUrl", "kind": "parameter", "value": BASE_URL}],
        "validationGates": [
            {"id": "home-hero-visible", "description": "Hero headline renders.", "required": True},
            {"id": "home-activity-slider", "description": "Activity slider renders.", "required": True},
        ],
        "unresolvedBlockingClarifications": [],
    }


def browser_skill_payload(*, activity_timeout_ms: int = 25000) -> dict[str, Any]:
    return {
        "path": f".proofsignal/skills/validate-{ALIAS}-flow.browser.md",
        "kind": "skill",
        "intent": {
            "id": f"skill.validate-{ALIAS}-flow",
            "version": "1.0.0",
            "browser": {
                "viewport": {"width": 1280, "height": 720},
                "targets": {
                    "hero": {"text": "Making you unstoppable."},
                    "activitySlide": {"css": ".chakra-container .swiper-slide"},
                },
                "steps": [
                    {"id": "open", "action": "navigate", "value": "{{parameters.baseUrl}}/"},
                    {"id": "wait-hero", "action": "waitForText", "target": "hero", "value": "Making you unstoppable.", "gateId": "home-hero-visible"},
                    {
                        "id": "scroll-to-activity",
                        "action": "scrollIntoView",
                        "target": "activitySlide",
                        "timeoutMs": activity_timeout_ms,
                        "gateId": "home-activity-slider",
                    },
                ],
                "assertions": [
                    {"id": "hero-visible", "kind": "visible", "target": "hero", "gateId": "home-hero-visible"},
                    {"id": "activity-visible", "kind": "visible", "target": "activitySlide", "gateId": "home-activity-slider"},
                ],
            },
        },
    }


def implement_payload() -> dict[str, Any]:
    return {
        "runRequest": {"path": f".proofsignal/run-requests/{ALIAS}.yaml"},
        "runtimeInputs": [{"name": "baseUrl", "kind": "parameter", "value": BASE_URL}],
        "skills": [browser_skill_payload()],
    }


def create_dogfood_ready_workspace(project: Path) -> None:
    init_workspace(project)
    record = UseCaseRecord(
        alias=ALIAS,
        title="Home Page Unauth",
        description="Validate the public home page for an unauthenticated visitor.",
        targetSurface="/",
        runRequest=ArtifactReference(path=f".proofsignal/run-requests/{ALIAS}.yaml", kind="run-request", id=f"request.{ALIAS}"),
        mainSkill=ArtifactReference(
            path=f".proofsignal/skills/validate-{ALIAS}-flow.browser.md",
            kind="skill",
            id=f"skill.validate-{ALIAS}-flow",
        ),
        runtimeInputs=[RuntimeInputRequirement(name="baseUrl", kind="parameter", value=BASE_URL)],
        profiles=[RunProfile(name="normal")],
        workflow={
            "stageHandoffDecisions": [
                {
                    "key": "browserTargetEnvironment",
                    "valueSummary": BASE_URL,
                    "sourceStage": "clarify",
                    "appliesTo": ALIAS,
                    "status": "active",
                }
            ]
        },
    )
    record.skills = [record.mainSkill]
    save_use_case(project, record)
    save_document(project / ".proofsignal" / "workflows" / "use-cases" / ALIAS / "plan.yaml", {
        "schemaVersion": "proofsignal-spec-workflow-artifact-plan/v1",
        "useCaseAlias": ALIAS,
        **browser_artifact_plan(),
    })
    save_document(project / ".proofsignal" / "run-requests" / f"{ALIAS}.yaml", {
        "schemaVersion": "qa-run-request/v1",
        "request": {"id": f"request.{ALIAS}", "name": "Home Page Unauth"},
        "target": "browser",
        "parameters": {"baseUrl": BASE_URL},
        "skills": [{"id": f"skill.validate-{ALIAS}-flow", "version": "1.0.0"}],
    })
    save_document(project / ".proofsignal" / "skills" / f"validate-{ALIAS}-flow.browser.md", {
        "schemaVersion": "qa-skill/v1",
        "id": f"skill.validate-{ALIAS}-flow",
        "version": "1.0.0",
        "kind": "browser",
    })
