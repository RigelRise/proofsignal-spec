from __future__ import annotations

from helpers import CliTestCase

from proofsignal_spec.workspace import artifacts
from proofsignal_spec.workspace.models import ArtifactReference, UseCaseRecord
from proofsignal_spec.workspace.repository import init_workspace, save_use_case
from proofsignal_spec.workspace.validation import validate_workspace


class WorkspaceModelTests(CliTestCase):
    def test_use_case_schema_and_external_reference_validation(self) -> None:
        init_workspace(self.project)
        record = UseCaseRecord(
            alias="login",
            title="Login",
            description="Login",
            runRequest=artifacts.link_external_artifact("external/login.yaml", "run-request"),
            mainSkill=artifacts.link_external_artifact("external/login.browser.md", "skill"),
            skills=[artifacts.link_external_artifact("external/login.browser.md", "skill")],
        )
        (self.project / "external").mkdir()
        (self.project / "external" / "login.yaml").write_text("schemaVersion: qa-run-request/v1\n", encoding="utf-8")
        (self.project / "external" / "login.browser.md").write_text("---\nschemaVersion: qa-skill/v1\n---\n", encoding="utf-8")
        save_use_case(self.project, record)

        findings = validate_workspace(self.project)
        self.assertFalse([item for item in findings if item["severity"] == "blocking"])

    def test_secret_policy_rejects_persisted_secret_values(self) -> None:
        init_workspace(self.project)
        record = UseCaseRecord(
            alias="login",
            title="Login",
            description="Login",
            runRequest=ArtifactReference(path=".proofsignal/run-requests/login.yaml", kind="run-request"),
            mainSkill=ArtifactReference(path=".proofsignal/skills/login.browser.md", kind="skill"),
            skills=[ArtifactReference(path=".proofsignal/skills/login.browser.md", kind="skill")],
            validation={"token": "fake-credential-value-abcdefghijklmnop"},
        )
        artifacts.write_generated_artifacts(self.project, record)
        save_use_case(self.project, record)

        findings = validate_workspace(self.project)
        self.assertTrue(any(item["code"] == "secret-looking-value" for item in findings))
