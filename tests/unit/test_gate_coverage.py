from __future__ import annotations

from verifysignal_spec.workflows.evidence import extract_browser_evidence, extract_core_runtime_evidence, normalize_planned_gates
from verifysignal_spec.workflows.gate_coverage import calculate_gate_coverage, coverage_status
from verifysignal_spec.workflows.models import (
    EvidenceInventory,
    GateCoverageResult,
    PlannedValidationGate,
    RepairRecommendation,
    RunProfileSettings,
    RuntimeEvidence,
    SafeRepairApplication,
    UseCaseValidationResult,
)


def test_required_page_result_gate_without_ui_evidence_is_network_only() -> None:
    gates, _warnings = normalize_planned_gates([{"id": "profile-card", "description": "Profile data card renders"}])
    evidence = extract_browser_evidence(
        {
            "steps": [
                {
                    "id": "network",
                    "action": "awaitNetwork",
                    "gateId": "profile-card",
                    "match": {"method": "POST", "urlContains": "graphql", "status": 200},
                }
            ]
        },
        known_gate_ids={"profile-card"},
    )

    coverage = calculate_gate_coverage(gates, evidence)

    assert coverage[0].status == "network-only"
    assert coverage_status("passed", coverage) == "incomplete"


def test_backend_gate_with_network_evidence_is_exercised() -> None:
    gates, _warnings = normalize_planned_gates([{"id": "profile-query", "description": "Profile backend query"}])
    evidence = extract_browser_evidence(
        {
            "steps": [
                {
                    "id": "network",
                    "action": "awaitNetwork",
                    "gateId": "profile-query",
                    "match": {"method": "POST", "urlContains": "graphql", "status": 200},
                }
            ]
        },
        known_gate_ids={"profile-query"},
    )

    coverage = calculate_gate_coverage(gates, evidence)

    assert coverage[0].status == "exercised"


def test_required_gate_with_ui_evidence_is_exercised() -> None:
    gates, _warnings = normalize_planned_gates([{"id": "profile-name", "description": "Profile name"}])
    evidence = extract_browser_evidence(
        {
            "targets": {"profileName": {"css": "h2", "domainSemantics": "Profile name"}},
            "assertions": [{"id": "assert-name", "kind": "visible", "target": "profileName", "gateId": "profile-name"}],
        },
        known_gate_ids={"profile-name"},
    )

    coverage = calculate_gate_coverage(gates, evidence)

    assert coverage[0].status == "exercised"
    assert coverage_status("passed", coverage) == "complete"


def test_workflow_validation_models_serialize_without_empty_fields() -> None:
    coverage = GateCoverageResult(
        gateId="overview-data-card",
        required=True,
        status="missing",
        missingEvidence=["mapped rendered-result evidence"],
    )
    profile = RunProfileSettings(profile="debug", headed=True, slowMoMs=900)
    recommendation = RepairRecommendation(
        id="repair-main-skill",
        category="safe-artifact-repair",
        safeCategory="main-skill-ordering",
        summary="Core executed helper skill before main skill.",
        action="Pass planned main skill first to Core.",
        affectedArtifacts=[".verifysignal/run-requests/profile-view-unauth.yaml"],
    )
    application = SafeRepairApplication(
        recommendationId="repair-main-skill",
        applied=True,
        changedArtifacts=[".verifysignal/run-requests/profile-view-unauth.yaml"],
        validationStatus="passed",
    )
    runtime_evidence = RuntimeEvidence(
        evidenceId="assert-profile-name",
        source="assertion",
        gateId="overview-data-card",
        status="passed",
        specificity="rendered-result",
    )
    result = UseCaseValidationResult(
        alias="profile-view-unauth",
        status="incomplete",
        coreStatus="passed",
        coverageStatus="incomplete",
        selectedMainSkill={"id": "skill.validate-profile-view-unauth-flow", "version": "2.1.0"},
        executedSkill={"id": "skill.discover-profile", "version": "1.1.0", "source": "core-public-result"},
        skillSelectionStatus="mismatch",
        gateCoverage=[coverage],
        missingRequiredGates=["overview-data-card"],
        profileSettings=profile,
        repairRecommendations=[recommendation],
        exitCode=2,
    )

    assert runtime_evidence.to_dict()["redactionStatus"] == "unknown"
    assert application.to_dict()["validationStatus"] == "passed"
    serialized = result.to_dict()
    assert serialized["status"] == "incomplete"
    assert serialized["profileSettings"] == {"profile": "debug", "headed": True, "slowMoMs": 900, "source": "default", "overrides": []}
    assert serialized["gateCoverage"][0]["missingEvidence"] == ["mapped rendered-result evidence"]
    assert serialized["repairRecommendations"][0]["safeCategory"] == "main-skill-ordering"


def test_public_core_evidence_drives_required_gate_coverage() -> None:
    gates, warnings = normalize_planned_gates(
        [
            {"id": "overview-data-card", "description": "Profile name renders", "required": True},
            {"id": "projects-tab-content", "description": "Projects tab renders", "required": True},
            {"id": "about-tab-content", "description": "About tab", "required": False},
        ]
    )
    inventory = extract_core_runtime_evidence(
        {
            "status": "passed",
            "data": {
                "gateEvidence": [
                    {"id": "assert-profile-name", "source": "assertion", "gateId": "overview-data-card", "status": "passed", "target": "profileName"},
                    {"id": "assert-project-card", "source": "assertion", "gateId": "projects-tab-content", "status": "passed", "target": "projectCard"},
                ]
            },
        },
        known_gate_ids={gate.id for gate in gates},
    )
    coverage = calculate_gate_coverage(gates, inventory)

    assert warnings == []
    assert coverage_status("passed", coverage) == "complete"
    assert {item.gateId: item.status for item in coverage}["about-tab-content"] == "missing"


def test_qa_report_steps_with_gate_ids_drive_runtime_coverage() -> None:
    gates, _warnings = normalize_planned_gates(
        [
            {"id": "overview-data-card", "description": "Profile name renders", "required": True},
            {"id": "projects-tab-content", "description": "Projects tab renders", "required": True},
        ]
    )
    inventory = extract_core_runtime_evidence(
        {
            "status": "passed",
            "data": {
                "report": {
                    "schemaVersion": "qa-report/v1",
                    "status": "passed",
                    "steps": [
                        {"id": "assert-profile-name", "status": "passed", "gateId": "overview-data-card", "evidence": []},
                        {"id": "assert-project-card", "status": "passed", "gateId": "projects-tab-content", "evidence": []},
                    ],
                }
            },
        },
        known_gate_ids={gate.id for gate in gates},
    )
    coverage = calculate_gate_coverage(gates, inventory)

    assert coverage_status("passed", coverage) == "complete"
    assert {item.gateId: item.uiEvidenceIds for item in coverage} == {
        "overview-data-card": ["assert-profile-name"],
        "projects-tab-content": ["assert-project-card"],
    }


def test_qa_report_failed_or_tolerated_steps_do_not_prove_coverage() -> None:
    gates, _warnings = normalize_planned_gates(
        [
            {"id": "overview-data-card", "description": "Profile name renders", "required": True},
            {"id": "projects-tab-content", "description": "Projects tab renders", "required": True},
        ]
    )
    inventory = extract_core_runtime_evidence(
        {
            "status": "passed",
            "data": {
                "report": {
                    "schemaVersion": "qa-report/v1",
                    "status": "passed",
                    "steps": [
                        {"id": "assert-profile-name", "status": "failed", "gateId": "overview-data-card", "evidence": []},
                        {
                            "id": "assert-project-card",
                            "status": "passed",
                            "gateId": "projects-tab-content",
                            "toleratedFailure": True,
                            "evidence": [],
                        },
                    ],
                }
            },
        },
        known_gate_ids={gate.id for gate in gates},
    )
    coverage = calculate_gate_coverage(gates, inventory)

    assert coverage_status("passed", coverage) == "incomplete"
    assert all(item.status == "missing" for item in coverage)


def test_qa_report_without_gate_ids_keeps_legacy_gate_evidence_fallback() -> None:
    gates, _warnings = normalize_planned_gates([{"id": "overview-data-card", "description": "Profile name renders", "required": True}])
    inventory = extract_core_runtime_evidence(
        {
            "status": "passed",
            "data": {
                "report": {
                    "schemaVersion": "qa-report/v1",
                    "status": "passed",
                    "steps": [{"id": "assert-profile-name", "status": "passed", "evidence": []}],
                },
                "gateEvidence": [
                    {"id": "legacy-profile-name", "source": "assertion", "gateId": "overview-data-card", "status": "passed", "target": "profileName"}
                ],
            },
        },
        known_gate_ids={gate.id for gate in gates},
    )
    coverage = calculate_gate_coverage(gates, inventory)

    assert coverage_status("passed", coverage) == "complete"
    assert coverage[0].uiEvidenceIds == ["legacy-profile-name"]


def test_qa_report_preconditions_with_gate_ids_drive_runtime_coverage() -> None:
    gates, _warnings = normalize_planned_gates([{"id": "session-precondition", "description": "Anonymous session", "required": True}])
    inventory = extract_core_runtime_evidence(
        {
            "status": "passed",
            "data": {
                "report": {
                    "schemaVersion": "qa-report/v1",
                    "status": "passed",
                    "steps": [],
                    "preconditions": [{"id": "anonymous-session", "status": "passed", "gateId": "session-precondition"}],
                }
            },
        },
        known_gate_ids={gate.id for gate in gates},
    )
    coverage = calculate_gate_coverage(gates, inventory)

    assert coverage_status("passed", coverage) == "complete"
    assert coverage[0].uiEvidenceIds == ["anonymous-session"]


def test_conditional_gate_without_established_condition_is_not_evaluated() -> None:
    gates = [PlannedValidationGate(id="featured-project", required=False, condition="Profile has featured project")]
    coverage = calculate_gate_coverage(gates, EvidenceInventory())

    assert coverage[0].status == "not-evaluated"
    assert coverage[0].required is False
    assert coverage_status("passed", coverage) == "complete"
