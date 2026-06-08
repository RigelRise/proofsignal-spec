from __future__ import annotations

import json
import os

from proofsignal_spec.core.executable_contract import project_core_contract
from proofsignal_spec.workspace.artifacts import render_run_request, render_skill
from proofsignal_spec.workspace.models import ArtifactReference, RuntimeInputRequirement, UseCaseRecord
from tests.fixtures.managed_runtime import current_core_contract_fixture_payload


def test_run_request_renders_core_credential_refs_without_values() -> None:
    record = UseCaseRecord(
        alias="add-collaboration-project",
        title="Add collaboration project",
        description="Create a collaboration project.",
        runRequest=ArtifactReference(path=".proofsignal/run-requests/add-collaboration-project.yaml", kind="run-request"),
        mainSkill=ArtifactReference(
            path=".proofsignal/skills/validate-add-collaboration-project-flow.browser.md",
            kind="skill",
            id="skill.validate-add-collaboration-project-flow",
            version="1.0.0",
        ),
        skills=[
            ArtifactReference(
                path=".proofsignal/skills/validate-add-collaboration-project-flow.browser.md",
                kind="skill",
                id="skill.validate-add-collaboration-project-flow",
                version="1.0.0",
            )
        ],
        runtimeInputs=[RuntimeInputRequirement(name="baseUrl", source="default")],
        credentialRefs={
            "e2eUser": {
                "source": "environment",
                "keys": {"email": "E2E_USER_EMAIL", "password": "E2E_USER_PASSWORD"},
            }
        },
    )

    rendered = json.loads(render_run_request(record, parameters={"baseUrl": "https://app.example.test"}))

    assert rendered["credentialRefs"]["e2eUser"]["source"] == "environment"
    assert rendered["credentialRefs"]["e2eUser"]["keys"]["email"] == "E2E_USER_EMAIL"
    assert "user@example.com" not in json.dumps(rendered)
    assert "password" not in rendered["parameters"]


def test_skill_renders_group_field_credential_placeholders() -> None:
    record = UseCaseRecord(
        alias="add-collaboration-project",
        title="Add collaboration project",
        description="Create a collaboration project.",
        credentialRefs={
            "e2eUser": {
                "source": "environment",
                "keys": {"email": "E2E_USER_EMAIL", "password": "E2E_USER_PASSWORD"},
            }
        },
    )
    skill = ArtifactReference(path=".proofsignal/skills/validate-add-collaboration-project-flow.browser.md", kind="skill")
    browser = {
        "targets": {"emailInput": {"testId": "email-input"}, "passwordInput": {"testId": "password-input"}},
        "steps": [
            {"id": "fill-email", "action": "fill", "target": "emailInput", "value": "{{credentials.e2eUser.email}}"},
            {"id": "fill-password", "action": "fill", "target": "passwordInput", "value": "{{credentials.e2eUser.password}}"},
        ],
    }

    rendered = render_skill(record, skill, browser=browser)

    assert "{{credentials.e2eUser.email}}" in rendered
    assert "{{credentials.e2eUser.password}}" in rendered
    assert "{{env.E2E_USER_EMAIL}}" not in rendered
    assert "{{credentials.E2E_USER_EMAIL}}" not in rendered


def test_core_credential_projection_does_not_include_environment_values() -> None:
    old_value = os.environ.get("E2E_USER_PASSWORD")
    os.environ["E2E_USER_PASSWORD"] = "super-secret-runtime-value"
    try:
        projection = project_core_contract(current_core_contract_fixture_payload())
    finally:
        if old_value is None:
            os.environ.pop("E2E_USER_PASSWORD", None)
        else:
            os.environ["E2E_USER_PASSWORD"] = old_value

    rendered = json.dumps(projection["sections"]["credentials"])

    assert "environment" in rendered
    assert "E2E_USER_PASSWORD" not in rendered
    assert "super-secret-runtime-value" not in rendered
