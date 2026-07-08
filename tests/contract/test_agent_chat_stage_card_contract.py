from __future__ import annotations

from verifysignal_spec.workflows.stage_cards import build_stage_card


def test_stage_card_contract_fields_and_marker() -> None:
    card = build_stage_card(
        stage_id="first-run-pass",
        title="First Run Passed",
        status_marker="[PASS]",
        summary="Core and Spec coverage passed.",
        why_it_matters="The first run now demonstrates the product end to end.",
        primary_evidence="coreBrowserStatus=passed, specCoverageStatus=complete, missingRequiredGates=[]",
        next_action="Choose the next validation.",
        secondary_refs=[".verifysignal/runs/home-page-unauth"],
    ).to_dict()

    for field in ["stageId", "title", "statusMarker", "summary", "whyItMatters", "primaryEvidence", "nextAction"]:
        assert card[field]
    assert card["statusMarker"] == "[PASS]"
    assert "raw log" not in card["primaryEvidence"].lower()
