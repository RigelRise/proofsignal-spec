from __future__ import annotations

from verifysignal_spec.workflows.models import (
    CorePublicContract,
    GateIntentState,
    RepairConfirmation,
    RunOutcomeSummary,
    RuntimeFeedbackFinding,
    StagePayloadValidationFinding,
    ValidationReadinessSummary,
    WorkflowStageContract,
)


def test_workflow_stage_contract_serializes_public_payload_guidance() -> None:
    contract = WorkflowStageContract(
        stage="specify",
        requiredFields=["surface", "behavior", "expectedOutcome"],
        optionalFields=["runtimeAssumptions", "targetEnvironment"],
        defaults={"status": "draft"},
        unsupportedFieldsPolicy="warn",
        examples=[{"surface": "/", "behavior": "Validate home.", "expectedOutcome": "Home renders."}],
        nextAction="verifysignal workflow persist specify --payload <payload.json> --json",
    )

    data = contract.to_dict()

    assert data["schemaVersion"] == "verifysignal-spec-stage-payload-contract/v1"
    assert data["stage"] == "specify"
    assert data["requiredFields"] == ["surface", "behavior", "expectedOutcome"]
    assert data["unsupportedFieldsPolicy"] == "warn"
    assert "installed package source" not in str(data).lower()


def test_stage_payload_finding_uses_actionable_public_fields() -> None:
    finding = StagePayloadValidationFinding(
        id="specify.expectedOutcome.missing",
        stage="specify",
        fieldPath="expectedOutcome",
        severity="blocked",
        message="Payload is missing expectedOutcome.",
        expectedContract="stagePayloadContracts.specify.requiredFields.expectedOutcome",
        recoveryAction="Add expectedOutcome or run /verifysignal-clarify before planning.",
    )

    assert finding.to_dict()["fieldPath"] == "expectedOutcome"
    assert finding.to_dict()["recoveryAction"].startswith("Add expectedOutcome")


def test_validation_readiness_summary_distinguishes_authored_mapping_from_browser_run() -> None:
    summary = ValidationReadinessSummary(
        alias="home-page-unauth",
        status="passed",
        skillSelectionStatus="matched",
        authoringCoherenceStatus="passed",
        authoredEvidenceCoverageStatus="complete",
        runtimeReadinessStatus="passed",
        fullBrowserFlowExecuted=False,
        nextAction="verifysignal run home-page-unauth --json",
    )

    data = summary.to_dict()

    assert data["authoredEvidenceCoverageStatus"] == "complete"
    assert data["fullBrowserFlowExecuted"] is False
    assert "run home-page-unauth" in data["nextAction"]


def test_run_outcome_summary_separates_core_browser_and_spec_coverage_status() -> None:
    summary = RunOutcomeSummary(
        alias="home-page-unauth",
        overallStatus="failed",
        coreBrowserStatus="failed",
        specCoverageStatus="diagnostic",
        selectedMainSkill={"id": "skill.validate-home-page-unauth-flow"},
        profile="normal",
        runId="request_home-page-unauth_1",
        failedStep="scroll-to-activity",
        nextAction="verifysignal repair home-page-unauth --json",
    )

    data = summary.to_dict()

    assert data["coreBrowserStatus"] == "failed"
    assert data["specCoverageStatus"] == "diagnostic"
    assert data["failedStep"] == "scroll-to-activity"


def test_runtime_feedback_and_repair_confirmation_serialize_non_secret_evidence() -> None:
    finding = RuntimeFeedbackFinding(
        id="finding.wait-flow.activity",
        source="report-inspection",
        category="wait-flow-issue",
        severity="failed",
        summary="Activity slider was still loading when the step searched for slides.",
        evidence=["failedStep=scroll-to-activity", "selector=.chakra-container .swiper-slide"],
        affectedGates=["home-activity-slider"],
        recommendedAction="implement-repair",
        confidence="high",
    )
    confirmation = RepairConfirmation(
        id="confirm.wait-flow.activity",
        findingId=finding.id,
        category=finding.category,
        confirmationSource="direct-user-answer",
        confirmationTextSummary="Developer confirmed extending the activity wait scope.",
        approvedScope=[".verifysignal/skills/validate-home-page-unauth-flow.browser.md"],
        affectedArtifacts=[".verifysignal/skills/validate-home-page-unauth-flow.browser.md"],
        revalidationRequired=True,
        status="pending",
    )

    assert finding.to_dict()["category"] == "wait-flow-issue"
    assert confirmation.to_dict()["revalidationRequired"] is True


def test_gate_intent_state_keeps_required_gate_stable_after_aborted_run() -> None:
    state = GateIntentState(
        gateId="home-activity-slider",
        required=True,
        conditionStatus="not-applicable",
        changeSource="plan",
        changeReason="Full behavior pass criteria requires activity content.",
    )

    data = state.to_dict()

    assert data["required"] is True
    assert data["changeSource"] == "plan"


def test_core_public_contract_serializes_compatibility_details() -> None:
    contract = CorePublicContract(
        operationName="run",
        schemaName="verifysignal.run/v1",
        schemaVersion=1,
        compatibilityStatus="compatible",
        incompatibilityBehavior="Block Core-facing workflows and ask the user to upgrade Core.",
    )

    data = contract.to_dict()

    assert data["contractVersion"] == "verifysignal-public-cli-json/v1"
    assert data["operationName"] == "run"
    assert data["schemaVersion"] == 1
