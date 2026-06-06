from __future__ import annotations

from tests.fixtures.managed_runtime import core_contract_fixture_payload
from proofsignal_spec.core.executable_contract import project_core_contract
from proofsignal_spec.workflows.browser_authoring import validate_browser_payload


def _projection() -> dict:
    return project_core_contract(
        core_contract_fixture_payload(
            browser_actions=[
                {"name": "navigate", "status": "stable", "requiredFields": ["value"]},
                {"name": "press", "status": "stable", "requiredFields": ["target", "value"]},
                {"name": "repeatUntil", "status": "unsupported", "requiredFields": ["until", "do"]},
            ]
        )
    )


def test_browser_validation_uses_core_added_stable_action() -> None:
    browser = {
        "targets": {"searchBox": {"testId": "search-box"}},
        "steps": [{"id": "press-enter", "action": "press", "target": "searchBox", "value": "Enter"}],
        "assertions": [],
    }

    assert validate_browser_payload(browser, core_contract=_projection()) == []


def test_browser_validation_rejects_core_removed_local_action() -> None:
    browser = {
        "targets": {"page": {"css": "body"}},
        "steps": [{"id": "legacy-repeat", "action": "repeatUntil", "until": {"text": "Done"}, "do": {"action": "click"}}],
        "assertions": [],
    }

    blockers = validate_browser_payload(browser, core_contract=_projection())

    assert blockers
    assert "repeatUntil" in blockers[0]
