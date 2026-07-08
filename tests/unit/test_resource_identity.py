from __future__ import annotations

from verifysignal_spec.workspace.models import ResourceIdentity, RuntimeInputRequirement


def test_resource_identity_allows_read_only_absence() -> None:
    assert ResourceIdentity.from_dict(None).required_for("none") is False
    assert ResourceIdentity.from_dict(None).required_for("authenticated-read") is False


def test_generated_input_identity_requires_refreshable_input() -> None:
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
        runtime_inputs=[RuntimeInputRequirement(name="projectTitle", source="generated", refreshOnRerunAfterCommit=True)],
    )

    assert findings == []
