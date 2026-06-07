from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


CORE_EXECUTABLE_CONTRACT_SOURCE = "core-public-contract"
CORE_CONTRACT_SCHEMA = "proofsignal.contracts/v1"


@dataclass(slots=True)
class ContractCompatibilityFinding:
    code: str
    message: str
    severity: str = "blocking"
    contractSection: str | None = None
    artifact: str | None = None
    path: str | None = None
    recoveryAction: str = "Upgrade ProofSignal Core or re-run proofsignal init for a compatible runtime."
    repairable: bool = False

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "recoveryAction": self.recoveryAction,
            "repairable": self.repairable,
        }
        if self.contractSection:
            data["contractSection"] = self.contractSection
        if self.artifact:
            data["artifact"] = self.artifact
        if self.path:
            data["path"] = self.path
        return data


@dataclass(slots=True)
class CoreContractProjection:
    runtimeIdentity: str | None = None
    coreVersion: str | None = None
    publicContractVersion: str | None = None
    schemaVersion: int | None = None
    sections: dict[str, Any] = field(default_factory=dict)
    stableOnlyAuthoring: bool = True
    findings: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": CORE_EXECUTABLE_CONTRACT_SOURCE,
            "runtimeIdentity": self.runtimeIdentity,
            "coreVersion": self.coreVersion,
            "publicContractVersion": self.publicContractVersion,
            "schemaVersion": self.schemaVersion,
            "sections": self.sections,
            "stableOnlyAuthoring": self.stableOnlyAuthoring,
            "findings": self.findings,
        }


class CommandContractReuse:
    """Per-command in-memory Core contract projection reuse."""

    def __init__(self) -> None:
        self._cache: dict[tuple[str | None, str | None, str | None], dict[str, Any]] = {}
        self.discovery_count = 0

    def get_or_discover(
        self,
        *,
        runtime_identity: str | None,
        core_version: str | None,
        public_contract_version: str | None,
        discover,
    ) -> dict[str, Any]:
        key = (runtime_identity, core_version, public_contract_version)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        raw = discover()
        self.discovery_count += 1
        projected = project_core_contract(
            raw,
            runtime_identity=runtime_identity,
            core_version=core_version,
            public_contract_version=public_contract_version,
        )
        self._cache[key] = projected
        return projected


def project_core_contract(
    raw: dict[str, Any],
    *,
    runtime_identity: str | None = None,
    core_version: str | None = None,
    public_contract_version: str | None = None,
) -> dict[str, Any]:
    findings = validate_core_contract(raw)
    data = raw.get("data") if isinstance(raw.get("data"), dict) else {}
    section_data = data.get("sections") if isinstance(data.get("sections"), dict) else {}
    sections = {
        "operations": _project_operations(section_data.get("operations")),
        "runRequest": _project_schema_section(section_data.get("runRequest")),
        "skill": _project_schema_section(section_data.get("skill")),
        "browserWorkflow": _project_browser_workflow(section_data.get("browserWorkflow")),
        "credentials": _project_credentials(section_data.get("credentials")),
        "placeholders": _project_placeholders(section_data.get("placeholders")),
        "reportCoverage": _project_report_coverage(section_data.get("reportCoverage")),
        "publicRedactionPolicy": _project_plain_section(section_data.get("publicRedactionPolicy")),
        "runtimeTrustHandoff": _project_plain_section(section_data.get("runtimeTrustHandoff")),
    }
    return CoreContractProjection(
        runtimeIdentity=runtime_identity,
        coreVersion=core_version,
        publicContractVersion=public_contract_version,
        schemaVersion=raw.get("schemaVersion") if isinstance(raw.get("schemaVersion"), int) else None,
        sections=sections,
        findings=[finding.to_dict() for finding in findings],
    ).to_dict()


def validate_core_contract(raw: dict[str, Any], *, required_sections: list[str] | None = None) -> list[ContractCompatibilityFinding]:
    findings: list[ContractCompatibilityFinding] = []
    if raw.get("schema") != CORE_CONTRACT_SCHEMA:
        findings.append(
            ContractCompatibilityFinding(
                code="core-contract.schema-incompatible",
                message="Core contracts response uses an incompatible schema.",
                contractSection="schema",
            )
        )
    if raw.get("status") not in {None, "passed"}:
        findings.append(
            ContractCompatibilityFinding(
                code="core-contract.discovery-failed",
                message="Core contracts operation did not pass.",
                contractSection="status",
            )
        )
    data = raw.get("data")
    if not isinstance(data, dict):
        return [
            *findings,
            ContractCompatibilityFinding(
                code="core-contract.data-malformed",
                message="Core contracts response data must be an object.",
                contractSection="data",
            ),
        ]
    section_data = data.get("sections") if isinstance(data.get("sections"), dict) else {}
    sections = required_sections or ["operations", "runRequest", "skill", "browserWorkflow", "credentials", "placeholders", "reportCoverage"]
    for section in sections:
        value = section_data.get(section)
        if value is None:
            findings.append(
                ContractCompatibilityFinding(
                    code="core-contract.section-missing",
                    message=f"Core contract section '{section}' is required for executable authoring.",
                    contractSection=section,
                )
            )
        elif section == "operations":
            if not isinstance(value, (dict, list)):
                findings.append(
                    ContractCompatibilityFinding(
                        code="core-contract.section-malformed",
                        message=f"Core contract section '{section}' is malformed.",
                        contractSection=section,
                    )
                )
        elif not isinstance(value, dict):
            findings.append(
                ContractCompatibilityFinding(
                    code="core-contract.section-malformed",
                    message=f"Core contract section '{section}' is malformed.",
                    contractSection=section,
                )
            )
    return findings


def browser_authoring_projection(projection: dict[str, Any]) -> dict[str, Any]:
    browser = projection.get("sections", {}).get("browserWorkflow", {})
    return {
        "schemaVersion": "proofsignal-browser-authoring-contract/v1",
        "source": CORE_EXECUTABLE_CONTRACT_SOURCE,
        "validActions": browser.get("validActions", []),
        "validAssertionKinds": browser.get("validAssertionKinds", []),
        "validNetworkMatchKeys": browser.get("validNetworkMatchKeys", []),
        "targetRules": browser.get("targetRules", {}),
        "actionRequirements": browser.get("actionRequirements", {}),
        "assertionRules": browser.get("assertionRules", {}),
        "gateEvidenceRules": browser.get("gateEvidenceRules", {}),
        "timingGuidance": browser.get("timingGuidance", []),
        "experimentalItems": browser.get("experimentalItems", {}),
    }


def _project_operations(value: Any) -> dict[str, Any]:
    operations = [item for item in _items(value) if _name(item)]
    stable = [item for item in operations if _status(item) == "stable"]
    return {
        "items": operations,
        "stable": stable,
        "byName": {_name(item): item for item in stable},
    }


def _project_schema_section(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    fields = [item for item in _items(value.get("fields")) if _name(item)]
    stable_fields = [item for item in fields if _status(item) == "stable"]
    return {
        **{key: val for key, val in value.items() if key != "fields"},
        "fields": stable_fields,
        "fieldNames": [_name(item) for item in stable_fields],
        "experimentalFields": [item for item in fields if _status(item) == "experimental"],
    }


def _project_browser_workflow(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    actions = [item for item in _items(value.get("actions")) if _name(item)]
    assertions = [item for item in _items(value.get("assertions")) if _name(item)]
    target_signals = [item for item in _items(value.get("targetSignals")) if _name(item)]
    network_keys = [item for item in _items(value.get("networkMatchKeys")) if _name(item)]
    metadata_keys = [item for item in _items(value.get("metadataKeys")) if _name(item)]
    stable_actions = [item for item in actions if _status(item) == "stable"]
    stable_assertions = [item for item in assertions if _status(item) == "stable"]
    stable_target_signals = [item for item in target_signals if _status(item) == "stable"]
    stable_network_keys = [item for item in network_keys if _status(item) == "stable"]
    stable_metadata_keys = [item for item in metadata_keys if _status(item) == "stable"]
    return {
        "validActions": sorted(_name(item) for item in stable_actions),
        "validAssertionKinds": sorted(_name(item) for item in stable_assertions),
        "validNetworkMatchKeys": sorted(_name(item) for item in stable_network_keys),
        "networkMetadataKeys": sorted(_name(item) for item in stable_metadata_keys),
        "targetSignalPriority": [_name(item) for item in stable_target_signals],
        "targetRules": {
            "stepsReferenceNamedTargets": "Step target values must be aliases declared under browser.targets, not inline selectors.",
            "targetSignalPriority": [_name(item) for item in stable_target_signals],
            "singlePrimarySignal": "Declare one primary selector signal per target.",
            "composition": _composition_rule(stable_target_signals),
        },
        "actionRequirements": {_name(item): {"required": item.get("requiredFields", [])} for item in stable_actions},
        "assertionRules": {_name(item): {"required": item.get("requiredFields", [])} for item in stable_assertions},
        "gateEvidenceRules": value.get("gateEvidenceRules") if isinstance(value.get("gateEvidenceRules"), dict) else {},
        "timingGuidance": value.get("timingGuidance") if isinstance(value.get("timingGuidance"), list) else [],
        "experimentalItems": {
            "actions": [item for item in actions if _status(item) == "experimental"],
            "assertions": [item for item in assertions if _status(item) == "experimental"],
            "targetSignals": [item for item in target_signals if _status(item) == "experimental"],
            "networkMatchKeys": [item for item in network_keys if _status(item) == "experimental"],
        },
    }


def _project_credentials(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    sources = [item for item in _items(value.get("sources")) if _name(item)]
    stable_sources = [item for item in sources if _status(item) == "stable"]
    return {
        **{key: val for key, val in value.items() if key != "sources"},
        "sources": stable_sources,
        "sourceNames": [_name(item) for item in stable_sources],
        "experimentalSources": [item for item in sources if _status(item) == "experimental"],
    }


def _project_placeholders(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    namespaces = [item for item in _items(value.get("supportedNamespaces")) if _name(item)]
    stable_namespaces = [item for item in namespaces if _status(item) == "stable"]
    return {
        **{key: val for key, val in value.items() if key != "supportedNamespaces"},
        "supportedNamespaces": stable_namespaces,
        "namespaceNames": [_name(item) for item in stable_namespaces],
    }


def _project_report_coverage(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _project_plain_section(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _composition_rule(items: list[dict[str, Any]]) -> str:
    for item in items:
        if _name(item) == "all" and isinstance(item.get("composition"), list):
            return "Use all only when multiple signals must match the same element. Supported entries: " + ", ".join(
                str(entry) for entry in item["composition"]
            )
    return "Use Core-declared target composition rules."


def _items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    items: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            items.append(item)
        elif isinstance(item, str) and item:
            items.append({"name": item})
    return items


def _name(item: dict[str, Any]) -> str:
    return str(item.get("name") or "")


def _status(item: dict[str, Any]) -> str:
    status = str(item.get("status") or "stable")
    return "stable" if status == "supported" else status
