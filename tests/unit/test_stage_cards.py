from __future__ import annotations

import pytest

from proofsignal_spec.workflows.models import AgentChatStageCard
from proofsignal_spec.workflows.stage_cards import build_stage_card


def test_stage_card_requires_known_status_marker_and_required_fields() -> None:
    card = AgentChatStageCard(
        stageId="recommendation",
        title="Recommended First Run",
        statusMarker="[RECOMMENDED]",
        summary="home-page-unauth is the safest first validation.",
        whyItMatters="It proves ProofSignal on a stable real user-facing page.",
        primaryEvidence="Ranked #1 because it needs no credentials and has simple rendered evidence.",
        nextAction="Ask the user to accept or skip.",
    )

    data = card.to_dict()

    assert data["statusMarker"] == "[RECOMMENDED]"
    assert data["stageId"] == "recommendation"
    assert "repairDetails" not in data


def test_repair_stage_card_requires_repair_details() -> None:
    with pytest.raises(ValueError, match="repairDetails"):
        AgentChatStageCard(
            stageId="repair",
            title="Repair Applied",
            statusMarker="[REPAIR]",
            summary="Wait strategy was adjusted.",
            whyItMatters="Safe repairs must explain what changed.",
            primaryEvidence="Before: 5s timeout. After: rendered slider wait.",
            nextAction="Revalidate and rerun.",
        )


def test_stage_card_rejects_raw_logs_and_secret_looking_content() -> None:
    with pytest.raises(ValueError, match="raw logs"):
        build_stage_card(
            stage_id="run",
            title="Run Failed",
            status_marker="[FAIL]",
            summary="Core run failed.",
            why_it_matters="The user needs a product-level diagnosis.",
            primary_evidence="raw log: locator timed out",
            next_action="Run repair.",
        )

    with pytest.raises(ValueError, match="Secret-looking"):
        build_stage_card(
            stage_id="target",
            title="Blocked Target",
            status_marker="[BLOCKED]",
            summary="Target includes a sensitive value.",
            why_it_matters="Stage cards must not expose secrets.",
            primary_evidence="https://example.test?token=abc123",
            next_action="Confirm a non-secret target.",
        )
