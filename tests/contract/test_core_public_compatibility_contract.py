from __future__ import annotations

from verifysignal_spec.core.contracts import REQUIRED_OPERATIONS, REQUIRED_PUBLIC_SCHEMA_NAMES, public_contract_summary, validate_version_response


def test_required_public_schema_names_are_declared() -> None:
    summary = public_contract_summary()

    assert "verifysignal-public-cli-json/v1" in summary["requiredPublicSchemaNames"]
    assert set(REQUIRED_PUBLIC_SCHEMA_NAMES) <= set(summary["requiredPublicSchemaNames"])


def test_missing_required_operation_blocks_compatibility() -> None:
    payload = {
        "data": {
            "verifysignalVersion": "0.2.0",
            "contractVersion": "verifysignal-public-cli-json/v1",
            "operations": [
                {"name": name, "schema": schema, "schemaVersion": version}
                for name, (schema, version) in REQUIRED_OPERATIONS.items()
                if name != "report.inspect"
            ],
        }
    }

    result = validate_version_response(payload)

    assert result.compatible is False
    assert "report.inspect" in result.missingOperations
