from __future__ import annotations

import json

from helpers import CliTestCase
from proofsignal_spec.workflows.stage_persistence import persist_stage
from tests.fixtures.workflows.workflow_dogfood_adjustments import minimal_specify_payload


class WorkflowPublicContractGuidanceTests(CliTestCase):
    def test_malformed_payload_error_names_public_field_and_recovery(self) -> None:
        result = persist_stage(
            self.project,
            "specify",
            alias="home-page-unauth",
            payload={
                "alias": "home-page-unauth",
                "surface": "/",
                "behavior": "Validate home page.",
                "customSourceReason": "Fixture.",
                "expectedOucome": "Typo should be flagged through public contract warnings.",
            },
        )

        self.assertEqual(result["status"], "invalid")
        blocker = result["blockers"][0]
        self.assertEqual(blocker["code"], "payload.missing-required-field")
        self.assertIn("expectedOutcome", blocker["message"])
        self.assertIn("stagePayloadContracts.specify.requiredFields", blocker["documentationRef"])
        self.assertIn("workflow info proofsignal-use-case --json", blocker["recoveryCommand"])
        self.assertTrue(any("expectedOucome" in warning for warning in result["warnings"]))

    def test_valid_payload_from_public_contract_persists_without_source_inspection(self) -> None:
        code, out, err = self.cli(["workflow", "info", "proofsignal-use-case", "--project", str(self.project), "--json"])
        self.assertEqual(code, 0, err)
        self.assertIn("stagePayloadContracts", json.loads(out))

        result = persist_stage(self.project, "specify", alias="home-page-unauth", payload=minimal_specify_payload())

        self.assertEqual(result["status"], "persisted")
        self.assertEqual(result["nextCommand"], "/proofsignal-clarify home-page-unauth")
