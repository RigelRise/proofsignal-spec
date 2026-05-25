from __future__ import annotations

from helpers import CliTestCase


class AuthorBrowserUseCaseTests(CliTestCase):
    def test_author_generates_artifacts_and_questions(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex"])
        self.assertEqual(self.cli(["author", "login", "Validate login.", "--project", str(self.project)])[0], 0)
        self.assertTrue((self.project / ".proofsignal" / "use-cases" / "login.yaml").exists())
        self.assertTrue((self.project / ".proofsignal" / "run-requests" / "login.yaml").exists())
        self.assertTrue((self.project / ".proofsignal" / "skills" / "login.browser.md").exists())

    def test_author_links_external_artifacts(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex"])
        external = self.project / "external"
        external.mkdir()
        (external / "login.yaml").write_text("schemaVersion: qa-run-request/v1\n", encoding="utf-8")
        (external / "login.browser.md").write_text("---\nschemaVersion: qa-skill/v1\n---\n", encoding="utf-8")
        self.assertEqual(
            self.cli([
                "author",
                "login",
                "Validate login.",
                "--project",
                str(self.project),
                "--run-request",
                "external/login.yaml",
                "--skill",
                "external/login.browser.md",
            ])[0],
            0,
        )
