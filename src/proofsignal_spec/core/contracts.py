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
    message: str = ""
    raw: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = {
            "compatible": self.compatible,
            "proofsignalVersion": self.proofsignalVersion,
            "contractVersion": self.contractVersion,
            "missingOperations": self.missingOperations or [],
            "message": self.message,
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
    for name, (schema, version) in REQUIRED_OPERATIONS.items():
        item = operation_map.get(name)
        if not item or item.get("schema") != schema or item.get("schemaVersion") != version:
            missing.append(name)
    compatible = contract_version == PUBLIC_CONTRACT_VERSION and not missing
    message = "Core contract is compatible." if compatible else "Core public CLI JSON contract is incompatible."
    return CompatibilityResult(
        compatible=compatible,
        proofsignalVersion=payload.get("proofsignalVersion"),
        contractVersion=contract_version,
        missingOperations=missing,
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
