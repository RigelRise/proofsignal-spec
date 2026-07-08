from __future__ import annotations

from verifysignal_spec.workspace.validation import validate_side_effect_lifecycle


def test_new_write_use_case_without_lifecycle_blocks() -> None:
    findings = validate_side_effect_lifecycle(None, side_effect_class="write", legacy=False)

    assert findings[0]["severity"] == "blocking"
    assert findings[0]["code"] == "side-effect-lifecycle-missing"


def test_legacy_write_use_case_without_lifecycle_warns_for_confirmation_path() -> None:
    findings = validate_side_effect_lifecycle(None, side_effect_class="write", legacy=True)

    assert findings[0]["severity"] == "warning"


def test_manual_cleanup_requires_instructions() -> None:
    findings = validate_side_effect_lifecycle(
        {"cleanupPolicy": "manual", "cleanupRequired": True},
        side_effect_class="write",
        legacy=False,
    )

    assert any(item["code"] == "side-effect-lifecycle-instructions-missing" for item in findings)
