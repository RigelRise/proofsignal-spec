from __future__ import annotations

from verifysignal_spec.workspace.models import NamedOutput
from verifysignal_spec.workspace.models import UseCaseRecord
from verifysignal_spec.workspace.validation import validate_use_case


def test_named_output_declaration_and_resolution_shape() -> None:
    output = NamedOutput(
        name="createdProjectUrl",
        value="https://app.example.test/project/verifysignal-collab-abc123",
        sourceBinding="finalUrl",
        publishedByRunId="run-1",
        useCaseAlias="add-collaboration-project",
        targetScope="https://app.example.test",
        resourceType="collaboration-project",
    )

    data = output.to_dict()

    assert data["name"] == "createdProjectUrl"
    assert data["sourceBinding"] == "finalUrl"
    assert data["publishedByRunId"] == "run-1"


def test_credential_values_cannot_be_published_as_named_outputs(tmp_path) -> None:
    record = UseCaseRecord(
        alias="publish-secret",
        title="Publish Secret",
        description="Invalid output fixture.",
        runtimeOutputs=[{"name": "apiToken", "source": "credential", "publishAsNamedOutput": True}],
    )

    findings = validate_use_case(tmp_path, record)

    assert any(item["code"] == "named-output-secret-name" for item in findings)
    assert any(item["code"] == "named-output-secret-source" for item in findings)
