from __future__ import annotations

from proofsignal_spec.workflows.write_safety import resolve_confirmation_signal_placeholders

from tests.helpers import assert_placeholder_finding


def test_resolves_parameter_placeholder_and_preserves_literal_signal() -> None:
    signals = [
        {
            "id": "published-title-confirmed",
            "type": "runtimeOutput",
            "reference": "publishedProjectTitleText",
            "expectedContains": "{{parameters.projectTitle}}",
        },
        {
            "id": "created-project-url-confirmed",
            "type": "runtimeOutput",
            "reference": "createdProjectUrl",
            "expectedContains": "/project/",
        },
    ]

    resolved, findings = resolve_confirmation_signal_placeholders(
        signals,
        {"projectTitle": "ProofSignal QA 20260619"},
    )

    assert findings == []
    assert resolved[0]["expectedContains"] == "ProofSignal QA 20260619"
    assert resolved[1]["expectedContains"] == "/project/"
    assert signals[0]["expectedContains"] == "{{parameters.projectTitle}}"


def test_resolves_multiple_parameter_placeholders_in_one_expected_value() -> None:
    resolved, findings = resolve_confirmation_signal_placeholders(
        [
            {
                "id": "summary-confirmed",
                "type": "runtimeOutput",
                "reference": "summary",
                "expectedContains": "{{ parameters.projectTitle }} by {{parameters.brandQuery}}",
            }
        ],
        {"projectTitle": "ProofSignal QA", "brandQuery": "Nike"},
    )

    assert findings == []
    assert resolved[0]["expectedContains"] == "ProofSignal QA by Nike"


def test_missing_parameter_placeholder_blocks_without_partial_resolution() -> None:
    resolved, findings = resolve_confirmation_signal_placeholders(
        [
            {
                "id": "published-title-confirmed",
                "type": "runtimeOutput",
                "reference": "publishedProjectTitleText",
                "expectedContains": "{{parameters.projectTitle}}",
            }
        ],
        {},
    )

    assert resolved[0]["expectedContains"] == "{{parameters.projectTitle}}"
    assert_placeholder_finding(
        findings[0],
        code="confirmation-placeholder-unresolved",
        placeholder="{{parameters.projectTitle}}",
    )


def test_unsupported_placeholder_namespace_blocks() -> None:
    _resolved, findings = resolve_confirmation_signal_placeholders(
        [
            {
                "id": "published-title-confirmed",
                "type": "runtimeOutput",
                "reference": "publishedProjectTitleText",
                "expectedContains": "{{credentials.feats.password}}",
            }
        ],
        {"projectTitle": "ProofSignal QA"},
    )

    assert_placeholder_finding(
        findings[0],
        code="confirmation-placeholder-unsupported-namespace",
        placeholder="{{credentials.feats.password}}",
    )
