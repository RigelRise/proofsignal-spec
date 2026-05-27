from __future__ import annotations

from proofsignal_spec.core.contracts import PUBLIC_CONTRACT_VERSION, REQUIRED_OPERATIONS, public_contract_summary, validate_version_response


def test_core_public_contract_declares_required_operations_and_schemas() -> None:
    summary = public_contract_summary()

    assert summary["contractVersion"] == PUBLIC_CONTRACT_VERSION
    assert {item["operationName"] for item in summary["requiredOperations"]} == {
        "version",
        "authoring-check",
        "run",
        "report.inspect",
    }
    assert summary["requiredOperationsByName"]["report.inspect"]["schemaName"] == "proofsignal.report-inspection/v1"


def test_core_contract_incompatibility_reports_missing_operation_names() -> None:
    payload = {
        "data": {
            "proofsignalVersion": "0.1.0",
            "contractVersion": PUBLIC_CONTRACT_VERSION,
            "operations": [
                {"name": name, "schema": schema, "schemaVersion": version}
                for name, (schema, version) in REQUIRED_OPERATIONS.items()
                if name != "report.inspect"
            ],
        }
    }

    result = validate_version_response(payload)

    assert result.compatible is False
    assert result.missingOperations == ["report.inspect"]
    assert result.to_dict()["requiredOperationsByName"]["run"]["schemaVersion"] == 1
