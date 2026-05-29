from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PUBLIC_CONTRACT_VERSION = "proofsignal-public-cli-json/v1"

REQUIRED_OPERATIONS = {
    "version": ("proofsignal.version/v1", 1),
    "authoring-check": ("proofsignal.authoring-check/v1", 1),
    "run": ("proofsignal.run/v1", 1),
    "report.inspect": ("proofsignal.report-inspection/v1", 1),
}

ALLOWED_CORE_STATUSES = {"passed", "failed", "blocked", "error"}


@dataclass(slots=True)
class CompatibilityResult:
    compatible: bool
    proofsignalVersion: str | None = None
    contractVersion: str | None = None
    missingOperations: list[str] | None = None
    incompatibleOperations: list[dict[str, Any]] | None = None
    message: str = ""
    raw: dict[str, Any] | None = None
    recoveryAction: str = "Upgrade ProofSignal Core or ProofSignal Spec to compatible public CLI JSON schemas."

    def to_dict(self) -> dict[str, Any]:
        compatibility_status = "compatible"
        if self.incompatibleOperations:
            compatibility_status = "incompatible"
        elif self.missingOperations:
            compatibility_status = "missing"
        elif not self.compatible:
            compatibility_status = "incompatible"
        data = {
            "compatible": self.compatible,
            "compatibilityStatus": compatibility_status,
            "proofsignalVersion": self.proofsignalVersion,
            "contractVersion": self.contractVersion,
            "missingOperations": self.missingOperations or [],
            "incompatibleOperations": self.incompatibleOperations or [],
            "message": self.message,
            "severity": "info" if self.compatible else "blocked",
            "recoveryAction": "" if self.compatible else self.recoveryAction,
        }
        data.update(public_contract_summary())
        return data


def public_contract_summary() -> dict[str, Any]:
    operations = [
        {
            "operationName": name,
            "schemaName": schema,
            "schemaVersion": version,
        }
        for name, (schema, version) in REQUIRED_OPERATIONS.items()
    ]
    return {
        "contractVersion": PUBLIC_CONTRACT_VERSION,
        "requiredOperations": operations,
        "requiredOperationsByName": {item["operationName"]: item for item in operations},
    }


def validate_version_response(data: dict[str, Any]) -> CompatibilityResult:
    payload = data.get("data", {})
    contract_version = payload.get("contractVersion")
    operations = payload.get("operations", [])
    operation_map = {item.get("name"): item for item in operations if isinstance(item, dict)}
    missing: list[str] = []
    incompatible: list[dict[str, Any]] = []
    for name, (schema, version) in REQUIRED_OPERATIONS.items():
        item = operation_map.get(name)
        if not item:
            missing.append(name)
            continue
        actual_schema = item.get("schema")
        actual_version = item.get("schemaVersion")
        if actual_schema != schema or actual_version != version:
            incompatible.append(
                {
                    "operationName": name,
                    "expectedSchema": schema,
                    "expectedSchemaVersion": version,
                    "actualSchema": actual_schema,
                    "actualSchemaVersion": actual_version,
                    "compatibilityStatus": "incompatible",
                    "severity": "blocked",
                    "recoveryAction": "Upgrade ProofSignal Core or ProofSignal Spec to compatible public CLI JSON schemas.",
                }
            )
    compatible = contract_version == PUBLIC_CONTRACT_VERSION and not missing
    if contract_version != PUBLIC_CONTRACT_VERSION:
        incompatible.append(
            {
                "operationName": "version",
                "expectedSchema": PUBLIC_CONTRACT_VERSION,
                "expectedSchemaVersion": None,
                "actualSchema": contract_version,
                "actualSchemaVersion": None,
                "compatibilityStatus": "incompatible",
                "severity": "blocked",
                "recoveryAction": "Upgrade ProofSignal Core or ProofSignal Spec to compatible public CLI JSON schemas.",
            }
        )
    compatible = compatible and not incompatible
    message = "Core contract is compatible." if compatible else "Core public CLI JSON contract is incompatible."
    return CompatibilityResult(
        compatible=compatible,
        proofsignalVersion=payload.get("proofsignalVersion"),
        contractVersion=contract_version,
        missingOperations=missing,
        incompatibleOperations=incompatible,
        message=message,
        raw=data,
    )


def normalize_status(data: dict[str, Any]) -> str:
    status = data.get("status")
    if status in ALLOWED_CORE_STATUSES:
        return status
    nested = data.get("data", {}).get("status")
    if nested in ALLOWED_CORE_STATUSES:
        return nested
    return "error"
