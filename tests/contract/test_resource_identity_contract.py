from __future__ import annotations

from verifysignal_spec.workspace.models import ResourceIdentity, RuntimeInputRequirement


def test_write_use_case_requires_resource_identity_before_implementation() -> None:
    identity = ResourceIdentity.from_dict(None)

    findings = identity.validate(side_effect_class="write", runtime_inputs=[])

    assert any(item["code"] == "resource-identity-missing" for item in findings)


def test_read_only_use_case_does_not_require_resource_identity() -> None:
    identity = ResourceIdentity.from_dict(None)

    assert identity.validate(side_effect_class="none", runtime_inputs=[]) == []


def test_generated_identity_input_must_reference_generated_runtime_input() -> None:
    identity = ResourceIdentity.from_dict(
        {
            "resourceType": "collaboration-project",
            "identityStrategy": "generated-input",
            "identityInput": "projectTitle",
            "collisionPolicy": "avoid",
            "targetScope": "https://app.example.test",
            "confidence": "confirmed",
        }
    )

    findings = identity.validate(
        side_effect_class="write",
        runtime_inputs=[RuntimeInputRequirement(name="projectTitle", source="default", value="VerifySignal collab seed")],
    )

    assert any(item["code"] == "resource-identity-input-not-generated" for item in findings)
