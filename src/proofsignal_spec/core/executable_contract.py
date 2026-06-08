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
    projection_findings: list[ContractCompatibilityFinding] = []
    data = raw.get("data") if isinstance(raw.get("data"), dict) else {}
    section_data = data.get("sections") if isinstance(data.get("sections"), dict) else {}
    sections = {
        "operations": _project_operations(section_data.get("operations")),
        "runRequest": _project_schema_section(section_data.get("runRequest"), "runRequest", projection_findings),
        "skill": _project_schema_section(section_data.get("skill"), "skill", projection_findings),
        "browserWorkflow": _project_browser_workflow(section_data.get("browserWorkflow"), projection_findings),
        "credentials": _project_credentials(section_data.get("credentials"), projection_findings),
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
        findings=[finding.to_dict() for finding in [*findings, *projection_findings]],
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


def _project_schema_section(
    value: Any,
    section_name: str = "schema",
    findings: list[ContractCompatibilityFinding] | None = None,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    fields = [item for item in _items(value.get("fields")) if _field_name(item)]
    stable_fields = [item for item in fields if _status(item) == "stable"]
    if findings is not None:
        _append_field_conflict_findings(section_name, stable_fields, findings)
    section_schema_version = value.get("schemaVersion") if isinstance(value.get("schemaVersion"), int) else None
    artifact_schema_version = _artifact_schema_version(value, stable_fields)
    projected = {
        **{key: val for key, val in value.items() if key != "fields"},
        "fields": stable_fields,
        "fieldNames": [_field_name(item) for item in stable_fields],
        "experimentalFields": [item for item in fields if _status(item) == "experimental"],
    }
    if section_schema_version is not None:
        projected["sectionSchemaVersion"] = section_schema_version
    if artifact_schema_version:
        projected["artifactSchemaVersion"] = artifact_schema_version
    return projected


def _artifact_schema_version(section: dict[str, Any], fields: list[dict[str, Any]]) -> str | None:
    explicit = section.get("artifactSchemaVersion")
    if isinstance(explicit, str) and explicit:
        return explicit
    legacy_schema = section.get("schemaVersion")
    if isinstance(legacy_schema, str) and legacy_schema.startswith("qa-"):
        return legacy_schema
    schema_field = next((item for item in fields if _field_name(item) == "schemaVersion"), None)
    if not isinstance(schema_field, dict):
        return None
    allowed_values = schema_field.get("allowedValues")
    if isinstance(allowed_values, list):
        return next((str(item) for item in allowed_values if isinstance(item, str) and item), None)
    for key in ("const", "value", "expected"):
        value = schema_field.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _append_field_conflict_findings(
    section_name: str,
    fields: list[dict[str, Any]],
    findings: list[ContractCompatibilityFinding],
) -> None:
    for field in fields:
        path = field.get("path")
        name = field.get("name")
        if isinstance(path, str) and isinstance(name, str) and path and name and path != name:
            findings.append(
                ContractCompatibilityFinding(
                    code="core-contract.canonical-legacy-conflict",
                    severity="warning",
                    message=f"Core {section_name} field descriptor exposes divergent path and name values; path is authoritative.",
                    contractSection=section_name,
                    path=f"{section_name}.fields.{path}",
                    recoveryAction="Use descriptor path as the field identifier; update legacy name aliases if they are still emitted.",
                )
            )


def _project_browser_workflow(value: Any, findings: list[ContractCompatibilityFinding] | None = None) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    actions = [item for item in _items(value.get("actions")) if _name(item)]
    assertions = [item for item in _items(value.get("assertions")) if _name(item)]
    target_signals = [item for item in _items(value.get("targetSignals")) if _name(item)]
    metadata_keys = [item for item in _items(value.get("metadataKeys")) if _name(item)]
    stable_actions = [item for item in actions if _status(item) == "stable"]
    stable_assertions = [item for item in assertions if _status(item) == "stable"]
    stable_target_signals = [item for item in target_signals if _status(item) == "stable"]
    stable_network_keys, experimental_network_keys = _project_network_match_keys(value, stable_actions, findings)
    stable_metadata_keys = [item for item in metadata_keys if _status(item) == "stable"]
    composition_signals = _project_target_composition_signals(value, stable_target_signals, findings)
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
            "composition": _composition_rule(composition_signals),
            "compositionSignals": composition_signals,
        },
        "actionRequirements": {_name(item): {"required": item.get("requiredFields", [])} for item in stable_actions},
        "assertionRules": {_name(item): {"required": item.get("requiredFields", [])} for item in stable_assertions},
        "gateEvidenceRules": value.get("gateEvidenceRules") if isinstance(value.get("gateEvidenceRules"), dict) else {},
        "timingGuidance": value.get("timingGuidance") if isinstance(value.get("timingGuidance"), list) else [],
        "experimentalItems": {
            "actions": [item for item in actions if _status(item) == "experimental"],
            "assertions": [item for item in assertions if _status(item) == "experimental"],
            "targetSignals": [item for item in target_signals if _status(item) == "experimental"],
            "networkMatchKeys": experimental_network_keys,
        },
        "nonExecutableItems": {
            "actions": _non_executable_items(actions),
            "assertions": _non_executable_items(assertions),
            "targetSignals": _non_executable_items(target_signals),
            "networkMatchKeys": _non_executable_items(
                [*(_items((next((item for item in stable_actions if _name(item) == "awaitNetwork"), {}) or {}).get("match", {}).get("keys"))), *_items(value.get("networkMatchKeys"))]
            ),
        },
    }


def _project_target_composition_signals(
    browser_workflow: dict[str, Any],
    stable_target_signals: list[dict[str, Any]],
    findings: list[ContractCompatibilityFinding] | None,
) -> list[str]:
    targets = browser_workflow.get("targets") if isinstance(browser_workflow.get("targets"), dict) else {}
    composition = targets.get("composition") if isinstance(targets.get("composition"), dict) else {}
    canonical = _string_names(composition.get("supportedSignals")) if isinstance(composition, dict) else []
    legacy = _legacy_composition_signals(stable_target_signals)
    if canonical:
        if legacy and set(legacy) != set(canonical) and findings is not None:
            findings.append(
                ContractCompatibilityFinding(
                    code="core-contract.canonical-legacy-conflict",
                    severity="warning",
                    message="Core browser workflow exposes divergent canonical target composition metadata and legacy target signal composition; canonical targets.composition.supportedSignals are authoritative.",
                    contractSection="browserWorkflow",
                    path="browserWorkflow.targets.composition.supportedSignals",
                    recoveryAction="Use Core-declared targets.composition.supportedSignals; update legacy target signal composition metadata if it is still emitted.",
                )
            )
        return canonical
    if legacy:
        return legacy
    return []


def _project_network_match_keys(
    browser_workflow: dict[str, Any],
    stable_actions: list[dict[str, Any]],
    findings: list[ContractCompatibilityFinding] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    await_network = next((item for item in stable_actions if _name(item) == "awaitNetwork"), None)
    match = await_network.get("match") if isinstance(await_network, dict) and isinstance(await_network.get("match"), dict) else {}
    canonical = [item for item in _items(match.get("keys")) if _name(item)] if isinstance(match, dict) else []
    legacy = [item for item in _items(browser_workflow.get("networkMatchKeys")) if _name(item)]
    stable_canonical = [item for item in canonical if _status(item) == "stable"]
    stable_legacy = [item for item in legacy if _status(item) == "stable"]
    experimental = [item for item in [*canonical, *legacy] if _status(item) == "experimental"]

    if stable_canonical:
        canonical_names = {_name(item) for item in stable_canonical}
        legacy_names = {_name(item) for item in stable_legacy}
        if legacy_names and legacy_names != canonical_names and findings is not None:
            findings.append(
                ContractCompatibilityFinding(
                    code="core-contract.canonical-legacy-conflict",
                    severity="warning",
                    message="Core browser workflow exposes divergent action-level and legacy top-level network match keys; action-level awaitNetwork.match.keys are authoritative.",
                    contractSection="browserWorkflow",
                    path="browserWorkflow.networkMatchKeys",
                    recoveryAction="Use Core-declared awaitNetwork.match.keys; update legacy aliases or remove them from the Core public contract.",
                )
            )
        return stable_canonical, experimental

    if stable_legacy:
        return stable_legacy, experimental

    if await_network is not None and findings is not None:
        findings.append(
            ContractCompatibilityFinding(
                code="core-contract.required-executable-metadata-missing",
                message="Core browser workflow declares executable awaitNetwork but does not expose supported match keys.",
                contractSection="browserWorkflow",
                path="browserWorkflow.actions.awaitNetwork.match.keys",
            )
        )
    return [], experimental


def _project_credentials(value: Any, findings: list[ContractCompatibilityFinding] | None = None) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    credential_refs = value.get("credentialRefs") if isinstance(value.get("credentialRefs"), dict) else {}
    canonical_sources = [item for item in _items(credential_refs.get("supportedSources")) if _name(item)] if isinstance(credential_refs, dict) else []
    legacy_sources = [item for item in _items(value.get("sources")) if _name(item)]
    sources = canonical_sources or legacy_sources
    stable_sources = [item for item in sources if _status(item) == "stable"]
    stable_canonical = [item for item in canonical_sources if _status(item) == "stable"]
    stable_legacy = [item for item in legacy_sources if _status(item) == "stable"]
    if stable_canonical and stable_legacy and {_name(item) for item in stable_canonical} != {_name(item) for item in stable_legacy} and findings is not None:
        findings.append(
            ContractCompatibilityFinding(
                code="core-contract.canonical-legacy-conflict",
                severity="warning",
                message="Core credentials expose divergent credentialRefs.supportedSources and legacy sources; credentialRefs.supportedSources are authoritative.",
                contractSection="credentials",
                path="credentials.credentialRefs.supportedSources",
                recoveryAction="Use credentialRefs.supportedSources; update or remove divergent legacy credential sources.",
            )
        )
    reference_shape = (
        credential_refs.get("referenceShape")
        if isinstance(credential_refs, dict) and isinstance(credential_refs.get("referenceShape"), str)
        else value.get("referenceShape")
    )
    placeholder_syntax = (
        credential_refs.get("placeholderSyntax")
        if isinstance(credential_refs, dict) and isinstance(credential_refs.get("placeholderSyntax"), str)
        else value.get("placeholderSyntax")
    )
    return {
        **{key: val for key, val in value.items() if key != "sources"},
        "sources": stable_sources,
        "sourceNames": [_name(item) for item in stable_sources],
        "experimentalSources": [item for item in sources if _status(item) == "experimental"],
        "referenceShape": reference_shape,
        "placeholderSyntax": placeholder_syntax,
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


def _composition_rule(signals: list[str]) -> str:
    if signals:
        return "Use all only when multiple signals must match the same element. Supported entries: " + ", ".join(signals)
    return "Use Core-declared target composition rules."


def _legacy_composition_signals(items: list[dict[str, Any]]) -> list[str]:
    for item in items:
        if _name(item) == "all" and isinstance(item.get("composition"), list):
            return [str(entry) for entry in item["composition"] if entry]
    return []


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


def _field_name(item: dict[str, Any]) -> str:
    return str(item.get("path") or item.get("name") or "")


def _status(item: dict[str, Any]) -> str:
    status = str(item.get("status") or "stable")
    return "stable" if status == "supported" else status


def _non_executable_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in items if _status(item) not in {"stable", "experimental"}]


def _string_names(value: Any) -> list[str]:
    return [_name(item) for item in _items(value) if _name(item)]
