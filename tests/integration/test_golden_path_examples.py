from __future__ import annotations

from tests.fixtures.workflows.golden_path_productization import create_canonical_example_workspaces


def test_canonical_example_workspaces_are_repeatable_and_classified(tmp_path) -> None:
    examples = create_canonical_example_workspaces(tmp_path)

    assert set(examples) == {
        "public-unauthenticated",
        "authenticated-secret-safe",
        "repairable-failure",
        "conditional-data",
    }
    assert examples["public-unauthenticated"]["expectedStatus"] == "pass"
    assert examples["authenticated-secret-safe"]["credentialPolicy"] == "runtime-reference-only"
    assert examples["repairable-failure"]["repairCategory"] == "wait-strategy"
    assert examples["conditional-data"]["allowedOutcomes"] == ["pass", "fail", "blocked", "not-evaluated"]
