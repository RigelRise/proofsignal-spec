from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from proofsignal_spec.workspace.repository import init_workspace, save_use_case
from proofsignal_spec.workspace.models import ArtifactReference, UseCaseRecord
from proofsignal_spec.workflows.models import ArtifactPlan
from proofsignal_spec.workflows.repository import save_artifact_plan


def create_real_run_guardrail_workspace(project: Path, alias: str = "profile-view-unauth") -> Path:
    init_workspace(project)
    record = UseCaseRecord(
        alias=alias,
        title="Profile View Unauth",
        description="Validate a public profile page.",
        runRequest=ArtifactReference(path=f".proofsignal/run-requests/{alias}.yaml", kind="run-request", id=f"request.{alias}", version="1.0.0"),
        mainSkill=ArtifactReference(
            path=".proofsignal/skills/validate-profile-view-unauth-flow.browser.md",
            kind="skill",
            id="skill.validate-profile-view-unauth-flow",
            version="1.0.0",
        ),
        skills=[
            ArtifactReference(path=".proofsignal/skills/validate-profile-view-unauth-flow.browser.md", kind="skill", id="skill.validate-profile-view-unauth-flow", version="1.0.0")
        ],
    )
    save_use_case(project, record)
    save_artifact_plan(
        project,
        ArtifactPlan(
            useCaseAlias=alias,
            runRequest=f".proofsignal/run-requests/{alias}.yaml",
            mainSkill=".proofsignal/skills/validate-profile-view-unauth-flow.browser.md",
            supportingSkills=[".proofsignal/skills/navigate-to-profile.browser.md"],
            runtimeInputs=[{"name": "baseUrl", "required": True, "default": "https://app.example.test"}],
            validationGates=profile_validation_gates(),
        ),
    )
    return project


def profile_validation_gates() -> list[dict[str, Any]]:
    return [
        {"id": "overview-data-card", "description": "Profile data card renders name, role, and location", "required": True},
        {"id": "overview-profile-query", "description": "Profile backend query completes successfully", "required": True},
        {"id": "projects-tab-content", "description": "Projects tab renders at least one project card", "required": True},
        {
            "id": "about-tab-content",
            "description": "About tab renders profile sections",
            "required": False,
            "condition": "Target profile exposes an About tab",
            "conditionEvaluation": "unmet",
        },
    ]


def coherent_profile_skill(path: str = ".proofsignal/skills/validate-profile-view-unauth-flow.browser.md") -> dict[str, Any]:
    return {
        "path": path,
        "kind": "skill",
        "browser": {
            "targets": {
                "profileName": {"css": "h2", "domainSemantics": "Profile name in profile data card"},
                "projectCard": {"css": "[data-testid='project-card']", "domainSemantics": "Project card in Projects tab"},
                "projectsTab": {"text": "Projects", "domainSemantics": "Projects tab trigger"},
            },
            "steps": [
                {"id": "open", "action": "navigate", "value": "{{parameters.baseUrl}}/profile/jordan-rivera/overview"},
                {
                    "id": "profile-query",
                    "action": "awaitNetwork",
                    "gateId": "overview-profile-query",
                    "match": {"method": "POST", "urlContains": "graphql", "status": 200, "requestBodyContains": "Profile"},
                },
                {"id": "profile-name", "action": "checkText", "target": "profileName", "value": "Jordan Rivera", "gateId": "overview-data-card"},
                {"id": "projects-tab", "action": "click", "target": "projectsTab"},
                {"id": "project-visible", "action": "checkText", "target": "projectCard", "value": "Project", "gateId": "projects-tab-content"},
            ],
            "assertions": [
                {"id": "assert-profile-name", "kind": "visible", "target": "profileName", "gateId": "overview-data-card"},
                {"id": "assert-project-card", "kind": "visible", "target": "projectCard", "gateId": "projects-tab-content"},
            ],
        },
    }


def navigation_only_skill(path: str = ".proofsignal/skills/validate-profile-view-unauth-flow.browser.md") -> dict[str, Any]:
    return {
        "path": path,
        "kind": "skill",
        "browser": {
            "targets": {"body": {"css": "body", "domainSemantics": "Whole page body"}},
            "steps": [
                {"id": "open", "action": "navigate", "value": "{{parameters.baseUrl}}/profile/jordan-rivera/overview"},
                {"id": "ok", "action": "awaitNetwork", "gateId": "overview-profile-query", "match": {"method": "POST", "urlContains": "graphql", "status": 200}},
            ],
            "assertions": [],
        },
    }


def run_request_payload(alias: str = "profile-view-unauth", skills_first: list[str] | None = None) -> dict[str, Any]:
    skills = skills_first or ["skill.validate-profile-view-unauth-flow"]
    return {
        "path": f".proofsignal/run-requests/{alias}.yaml",
        "kind": "run-request",
        "parameters": {"baseUrl": "https://app.example.test"},
        "content": json.dumps(
            {
                "schemaVersion": "qa-run-request/v1",
                "request": {"id": f"request.{alias}", "name": alias},
                "target": "browser",
                "validationScope": "feature-level",
                "skills": [{"id": item, "version": "1.0.0"} for item in skills],
                "parameters": {"baseUrl": "https://app.example.test"},
            }
        ),
    }
