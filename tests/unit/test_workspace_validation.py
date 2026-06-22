from __future__ import annotations

from proofsignal_spec.workspace.validation import validate_side_effect_declaration

from tests.fixtures.workflows.side_effect_contract_alignment import templated_confirmation_policy


def test_confirmation_parameter_placeholder_is_valid_when_runtime_input_declares_value() -> None:
    findings = validate_side_effect_declaration(
        templated_confirmation_policy(),
        rerun_policy={"afterNoCommit": "allowed", "afterCommit": "allowed-with-new-inputs", "refreshRuntimeInputs": ["projectTitle"]},
        runtime_outputs=[{"name": "publishedProjectTitleText", "source": "dom", "target": "publishedProjectTitle", "extract": "textContent"}],
        runtime_inputs=[{"name": "projectTitle", "source": "generated", "value": "ProofSignal QA", "refreshOnRerunAfterCommit": True}],
    )

    assert "confirmation-placeholder-unresolved" not in {item["code"] for item in findings}


def test_confirmation_placeholder_secret_like_resolved_value_blocks() -> None:
    findings = validate_side_effect_declaration(
        templated_confirmation_policy(placeholder="{{parameters.apiToken}}"),
        rerun_policy={"afterNoCommit": "allowed", "afterCommit": "allowed-with-new-inputs", "refreshRuntimeInputs": ["projectTitle"]},
        runtime_outputs=[{"name": "publishedProjectTitleText", "source": "dom", "target": "publishedProjectTitle", "extract": "textContent"}],
        runtime_inputs=[{"name": "apiToken", "source": "default", "value": "Bearer very-secret-token-value"}],
    )

    assert any(item["code"] == "confirmation-placeholder-secret-value" for item in findings)
