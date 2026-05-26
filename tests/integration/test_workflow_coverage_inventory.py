from __future__ import annotations

import json

from helpers import CliTestCase

from tests.fixtures.workflows.guardrails import stage_payload, write_payload


class WorkflowCoverageInventoryIntegrationTests(CliTestCase):
    def test_continue_scope_updates_inventory_without_losing_existing_items(self) -> None:
        base_payload = stage_payload(
            "understand",
            payload={
                "repositorySummary": "Example app.",
                "localStartInstructions": "npm run dev",
                "generatedGitHash": "abc123",
                "coverageInventory": {
                    "generatedAt": "2026-05-25T00:00:00Z",
                    "generatedGitHash": "abc123",
                    "gitAvailable": True,
                    "items": [{"id": "route-a", "surfaceType": "route", "path": "/a", "title": "A"}],
                    "candidateUseCases": [],
                    "uncoveredAreas": ["app/b"],
                },
            },
        )
        self.cli([
            "workflow",
            "persist",
            "understand",
            "--project",
            str(self.project),
            "--scope",
            "all",
            "--payload",
            str(write_payload(self.project, "understand-a", base_payload)),
            "--json",
        ])
        next_payload = stage_payload(
            "understand",
            payload={
                "repositorySummary": "Example app.",
                "localStartInstructions": "npm run dev",
                "generatedGitHash": "abc123",
                "coverageInventory": {
                    "generatedAt": "2026-05-25T00:01:00Z",
                    "generatedGitHash": "abc123",
                    "gitAvailable": True,
                    "items": [{"id": "route-b", "surfaceType": "route", "path": "/b", "title": "B"}],
                    "candidateUseCases": [],
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
            "continue",
            "--payload",
            str(write_payload(self.project, "understand-b", next_payload)),
            "--json",
        ])
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["status"], "persisted")
        context = json.loads((self.project / ".proofsignal/product-context.yaml").read_text())
        self.assertEqual({item["id"] for item in context["coverageInventory"]["items"]}, {"route-a", "route-b"})
