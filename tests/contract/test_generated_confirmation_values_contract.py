from __future__ import annotations

import json

from verifysignal_spec.commands.run import _prepared_run_request_path
from verifysignal_spec.workspace.validation import validate_side_effect_declaration

from tests.fixtures.workflows.side_effect_contract_alignment import templated_confirmation_policy
from tests.helpers import assert_placeholder_finding, assert_prepared_confirmation_value


def test_prepared_run_request_contains_concrete_confirmation_expected_value(tmp_path) -> None:
    request = tmp_path / "run-request.json"
    request.write_text(
        json.dumps(
            {
                "schemaVersion": "qa-run-request/v1",
                "parameters": {"baseUrl": "https://example.test"},
                "sideEffectPolicy": templated_confirmation_policy(),
            }
        ),
        encoding="utf-8",
    )

    prepared = _prepared_run_request_path(
        request,
        tmp_path / "runs",
        "add-collaboration-project-20260619T174233Z",
        {"projectTitle": "VerifySignal QA 20260619"},
    )

    document = json.loads(prepared.read_text(encoding="utf-8"))
    assert_prepared_confirmation_value(
        document,
        "published-title-confirmed",
        "expectedContains",
        "VerifySignal QA 20260619",
    )
    assert_prepared_confirmation_value(document, "created-project-url-confirmed", "expectedContains", "/project/")


def test_unresolved_confirmation_placeholder_finding_shape_is_guided() -> None:
    findings = validate_side_effect_declaration(
        templated_confirmation_policy(placeholder="{{parameters.missingTitle}}"),
        rerun_policy={"afterNoCommit": "allowed", "afterCommit": "allowed-with-new-inputs", "refreshRuntimeInputs": ["projectTitle"]},
        runtime_outputs=[{"name": "publishedProjectTitleText", "source": "dom", "target": "publishedProjectTitle", "extract": "textContent"}],
        runtime_inputs=[{"name": "projectTitle", "source": "generated", "value": "VerifySignal QA", "refreshOnRerunAfterCommit": True}],
    )

    finding = next(item for item in findings if item["code"] == "confirmation-placeholder-unresolved")
    assert_placeholder_finding(finding, code="confirmation-placeholder-unresolved", placeholder="{{parameters.missingTitle}}")
    assert finding["signalId"] == "published-title-confirmed"
    assert finding["recoveryCommand"].startswith("verifysignal workflow")
