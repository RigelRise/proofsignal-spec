from __future__ import annotations

import json

from helpers import CliTestCase

from tests.fixtures.workflows.guardrails import stage_payload, write_payload


class WorkflowStagePersistenceContractTests(CliTestCase):
    def test_workflow_info_defaults_to_current_workflow_and_includes_browser_authoring_contract(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex", "--json"])

        code, out, err = self.cli(["workflow", "info", "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        result = json.loads(out)
        self.assertEqual(result["schemaVersion"], "proofsignal-spec-workflow-info/v1")
        self.assertEqual(result["workflowId"], "proofsignal-use-case")
        contract = result["browserAuthoringContract"]
        self.assertIn("navigate", contract["validActions"])
        self.assertIn("text", contract["validAssertionKinds"])
        self.assertIn("method", contract["validNetworkMatchKeys"])
        self.assertIn("stepsReferenceNamedTargets", contract["targetRules"])

    def test_understand_persists_product_context_and_inventory(self) -> None:
        payload = stage_payload(
            "understand",
            payload={
                "repositorySummary": "Example app.",
                "localStartInstructions": "npm run dev",
                "generatedGitHash": "abc123",
                "coverageInventory": {
                    "generatedAt": "2026-05-25T00:00:00Z",
                    "generatedGitHash": "abc123",
                    "gitAvailable": True,
                    "items": [
                        {
                            "id": "route-login",
                            "surfaceType": "route",
                            "path": "/login",
                            "title": "Login",
                            "sourceRefs": ["app/login/page.tsx"],
                            "candidateUseCaseRefs": ["login"],
                            "priority": "high",
                        }
                    ],
                    "candidateUseCases": [
                        {
                            "alias": "login",
                            "surface": "/login",
                            "behavior": "Validate login.",
                            "sourceInventoryItems": ["route-login"],
                            "rationale": "Critical auth entry point.",
                            "confidence": "high",
                        }
                    ],
                },
            },
        )
        code, out, err = self.cli([
            "workflow",
            "persist",
            "understand",
            "--project",
            str(self.project),
            "--scope",
            "all",
            "--payload",
            str(write_payload(self.project, "understand", payload)),
            "--json",
        ])
        self.assertEqual(code, 0, err)
        result = json.loads(out)
        self.assertEqual(result["schemaVersion"], "proofsignal-spec-workflow-stage-persistence-result/v1")
        self.assertEqual(result["status"], "persisted")
        self.assertTrue((self.project / ".proofsignal/product-context.yaml").exists())
        self.assertTrue((self.project / ".proofsignal/workflows/understanding.md").exists())

    def test_plan_blocks_unresolved_environment_dependent_clarification(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex", "--json"])
        specify_payload = stage_payload(
            "specify",
            payload={
                "alias": "login",
                "surface": "/login",
                "behavior": "Validate login.",
                "expectedOutcome": "User reaches the dashboard.",
                "customSourceReason": "Manual test fixture.",
            },
        )
        self.cli([
            "workflow",
            "persist",
            "specify",
            "--alias",
            "login",
            "--project",
            str(self.project),
            "--payload",
            str(write_payload(self.project, "specify", specify_payload)),
            "--json",
        ])
        clarify_payload = stage_payload(
            "clarify",
            payload={
                "alias": "login",
                "questions": [
                    {
                        "id": "q1",
                        "prompt": "Which credential group should be used?",
                        "reason": "Credential context changes runtime setup.",
                        "affects": "credentials",
                        "environmentDependent": True,
                    }
                ],
                "answers": [],
                "blockingQuestionsResolved": False,
            },
        )
        self.cli([
            "workflow",
            "persist",
            "clarify",
            "--alias",
            "login",
            "--project",
            str(self.project),
            "--payload",
            str(write_payload(self.project, "clarify", clarify_payload)),
            "--json",
        ])

        plan_payload = stage_payload(
            "plan",
            payload={
                "alias": "login",
                "runRequest": ".proofsignal/run-requests/login.yaml",
                "reusableSkills": [".proofsignal/skills/login.browser.md"],
                "runtimeInputs": [],
                "unresolvedBlockingClarifications": [{"id": "q1"}],
            },
        )
        code, out, err = self.cli([
            "workflow",
            "persist",
            "plan",
            "--alias",
            "login",
            "--project",
            str(self.project),
            "--payload",
            str(write_payload(self.project, "plan", plan_payload)),
            "--json",
        ])
        self.assertEqual(code, 2, err)
        result = json.loads(out)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["blockers"][0]["code"], "clarification.unresolved-blocking")

    def test_workflow_show_and_status_alias_read_persisted_use_case_context(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex", "--json"])
        specify_payload = stage_payload(
            "specify",
            payload={
                "alias": "login",
                "surface": "/login",
                "behavior": "Validate login.",
                "expectedOutcome": "User reaches the dashboard.",
                "customSourceReason": "Manual test fixture.",
            },
        )
        code, out, err = self.cli([
            "workflow",
            "persist",
            "specify",
            "--alias",
            "login",
            "--project",
            str(self.project),
            "--payload",
            str(write_payload(self.project, "specify", specify_payload)),
            "--json",
        ])
        self.assertEqual(code, 0, err)

        code, out, err = self.cli(["workflow", "show", "--alias", "login", "--project", str(self.project), "--json"])
        self.assertEqual(code, 0, err)
        shown = json.loads(out)
        self.assertEqual(shown["schemaVersion"], "proofsignal-spec-workflow-show/v1")
        self.assertEqual(shown["useCase"]["alias"], "login")
        self.assertTrue(shown["documents"]["specify"]["exists"])
        self.assertIn("Validate login.", shown["documents"]["specify"]["content"])

        code, out, err = self.cli(["workflow", "status", "--alias", "login", "--project", str(self.project), "--json"])
        self.assertEqual(code, 0, err)
        status = json.loads(out)
        self.assertEqual(status["schemaVersion"], "proofsignal-spec-workflow-status/v1")
        self.assertEqual(status["useCaseAlias"], "login")

        code, out, err = self.cli(["workflow", "status", "login", "--project", str(self.project), "--json"])
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["useCaseAlias"], "login")
