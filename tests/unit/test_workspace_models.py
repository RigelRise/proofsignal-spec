from __future__ import annotations

from helpers import CliTestCase

from proofsignal_spec.workspace import artifacts
from proofsignal_spec.workspace.models import ArtifactReference, UseCaseRecord
from proofsignal_spec.workspace.models import RuntimeInputRequirement
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

    def test_generated_artifacts_use_core_compliant_skill_envelopes(self) -> None:
        init_workspace(self.project)
        record = UseCaseRecord(
            alias="login",
            title="Login",
            description="Validate login.",
            runRequest=ArtifactReference(path=".proofsignal/run-requests/login.yaml", kind="run-request", id="request.login"),
            mainSkill=ArtifactReference(path=".proofsignal/skills/login.browser.md", kind="skill", id="skill.login"),
            skills=[ArtifactReference(path=".proofsignal/skills/login.browser.md", kind="skill", id="skill.login")],
            runtimeInputs=[RuntimeInputRequirement(name="baseUrl")],
        )
        artifacts.write_generated_artifacts(self.project, record, overwrite=True)
        run_request = (self.project / ".proofsignal/run-requests/login.yaml").read_text()
        skill = (self.project / ".proofsignal/skills/login.browser.md").read_text()
        self.assertIn('"schemaVersion": "qa-run-request/v1"', run_request)
        self.assertIn('"parameters"', run_request)
        self.assertIn("schemaVersion: qa-skill/v1", skill)
        self.assertIn("browser:", skill)
        self.assertIn("value: \"{{parameters.baseUrl}}\"", skill)

    def test_use_case_serializes_source_only_skills_and_composition_decisions(self) -> None:
        record = UseCaseRecord(
            alias="brands-search-authenticated",
            title="Brands Search Authenticated",
            description="Validate authenticated brands search.",
            runRequest=ArtifactReference(path=".proofsignal/run-requests/brands.yaml", kind="run-request"),
            mainSkill=ArtifactReference(path=".proofsignal/skills/brands-main.browser.md", kind="skill", id="skill.brands-main"),
            skills=[
                ArtifactReference(path=".proofsignal/skills/brands-main.browser.md", kind="skill", id="skill.brands-main"),
                ArtifactReference(path=".proofsignal/skills/login.browser.md", kind="skill", id="skill.login"),
            ],
            sourceOnlySkills=[
                ArtifactReference(path=".proofsignal/skills/login.browser.md", kind="skill", id="skill.login"),
            ],
            skillComposition={
                "mode": "inline-into-main",
                "sourceSkillPaths": [".proofsignal/skills/login.browser.md"],
                "mainSkillPath": ".proofsignal/skills/brands-main.browser.md",
                "credentialReferencePolicy": "preserve-placeholders",
            },
        )

        restored = UseCaseRecord.from_dict(record.to_dict())

        self.assertEqual(restored.sourceOnlySkills[0].path, ".proofsignal/skills/login.browser.md")
        self.assertEqual(restored.skillComposition["mode"], "inline-into-main")
