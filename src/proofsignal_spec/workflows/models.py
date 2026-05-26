from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


WorkflowStatus = Literal["not-started", "running", "paused", "blocked", "failed", "completed"]
StageStatus = Literal["pending", "running", "completed", "blocked", "skipped", "failed"]
GateDecisionValue = Literal["approved", "rejected"]
GateConditionEvaluation = Literal["met", "unmet", "not-evaluated"]
GateCoverageStatus = Literal[
    "exercised",
    "missing",
    "conditional-met",
    "conditional-unmet",
    "not-evaluated",
    "screenshot-only",
    "network-only",
    "unmapped",
]

WORKFLOW_ID = "proofsignal-use-case"
WORKFLOW_RUN_SCHEMA = "proofsignal-spec-workflow-run/v1"
WORKFLOW_STATE_SCHEMA = "proofsignal-spec-workflow-state/v1"
WORKFLOW_TASK_SET_SCHEMA = "proofsignal-spec-workflow-tasks/v1"
WORKFLOW_ARTIFACT_PLAN_SCHEMA = "proofsignal-spec-workflow-artifact-plan/v1"
WORKFLOW_PREREQUISITE_CHECK_SCHEMA = "proofsignal-spec-workflow-prerequisite-check/v1"
WORKFLOW_CAPABILITY_SCHEMA = "proofsignal-spec-workflow-capability/v1"
WORKFLOW_GUARDRAILS_CAPABILITY = "workflow.guardrails/v1"
WORKFLOW_STAGE_PERSISTENCE_RESULT_SCHEMA = "proofsignal-spec-workflow-stage-persistence-result/v1"
WORKFLOW_VALIDATION_READINESS_SCHEMA = "proofsignal-spec-validation-readiness/v1"
WORKFLOW_MIGRATION_RESULT_SCHEMA = "proofsignal-spec-workflow-migration-result/v1"
WORKFLOW_UNDERSTANDING_COMMIT_THRESHOLD = 10
WORKFLOW_UNDERSTANDING_MAX_AGE_DAYS = 7
WORKFLOW_STAGES = ["understand", "specify", "clarify", "plan", "tasks", "implement", "validate", "run", "repair"]
COMMAND_STAGES = [*WORKFLOW_STAGES, "list"]


def clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return value


@dataclass(slots=True)
class ReadinessBlocker:
    code: str
    severity: Literal["warning", "error", "blocker"] = "blocker"
    message: str = ""
    recoveryCommand: str | None = None
    documentationRef: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReadinessBlocker":
        return cls(
            code=str(data.get("code", "")),
            severity=data.get("severity", "blocker"),
            message=str(data.get("message", "")),
            recoveryCommand=data.get("recoveryCommand"),
            documentationRef=data.get("documentationRef"),
        )

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class WorkflowContractCapability:
    stage: str
    supported: bool = True
    minimumRequiredVersion: str = "0.0.0"
    currentVersion: str | None = None
    missingCommands: list[str] = field(default_factory=list)
    blockers: list[ReadinessBlocker] = field(default_factory=list)
    schemaVersion: str = WORKFLOW_CAPABILITY_SCHEMA
    requiredCapability: str = WORKFLOW_GUARDRAILS_CAPABILITY

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["blockers"] = [item.to_dict() for item in self.blockers]
        return clean(data)


@dataclass(slots=True)
class ManagedWorkspaceArtifact:
    path: str
    kind: str
    schemaVersion: str | None = None
    managed: bool = True
    checksum: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class StagePersistenceRequest:
    stage: str
    alias: str | None = None
    scope: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StagePersistenceRequest":
        return cls(
            stage=str(data.get("stage", "")),
            alias=data.get("alias"),
            scope=data.get("scope"),
            payload=dict(data.get("payload", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class StagePersistenceResult:
    stage: str
    alias: str | None = None
    status: Literal["persisted", "blocked", "invalid"] = "persisted"
    writtenArtifacts: list[ManagedWorkspaceArtifact] = field(default_factory=list)
    updatedRecords: list[str] = field(default_factory=list)
    blockers: list[ReadinessBlocker] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    nextCommand: str | None = None
    schemaVersion: str = WORKFLOW_STAGE_PERSISTENCE_RESULT_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["writtenArtifacts"] = [item.to_dict() for item in self.writtenArtifacts]
        data["blockers"] = [item.to_dict() for item in self.blockers]
        return clean(data)


@dataclass(slots=True)
class InventoryPass:
    scope: str
    startedAt: str
    completedAt: str | None = None
    coveredAreas: list[str] = field(default_factory=list)
    uncoveredAreas: list[str] = field(default_factory=list)
    sourceFilesVisited: int = 0
    status: Literal["complete", "partial", "interrupted"] = "partial"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InventoryPass":
        return cls(
            scope=str(data.get("scope", "all")),
            startedAt=str(data.get("startedAt", "")),
            completedAt=data.get("completedAt"),
            coveredAreas=[str(item) for item in data.get("coveredAreas", [])],
            uncoveredAreas=[str(item) for item in data.get("uncoveredAreas", [])],
            sourceFilesVisited=int(data.get("sourceFilesVisited", 0) or 0),
            status=data.get("status", "partial"),
        )

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class CoverageInventoryItem:
    id: str
    surfaceType: str
    path: str
    title: str
    sourceRefs: list[str] = field(default_factory=list)
    userFacing: bool = True
    inventoryStatus: Literal["covered", "excluded", "stale", "uncovered"] = "covered"
    exclusionReason: str | None = None
    candidateUseCaseRefs: list[str] = field(default_factory=list)
    priority: Literal["critical", "high", "medium", "low"] = "medium"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CoverageInventoryItem":
        return cls(
            id=str(data.get("id", "")),
            surfaceType=str(data.get("surfaceType", "route")),
            path=str(data.get("path", "")),
            title=str(data.get("title", "")),
            sourceRefs=[str(item) for item in data.get("sourceRefs", [])],
            userFacing=bool(data.get("userFacing", True)),
            inventoryStatus=data.get("inventoryStatus", "covered"),
            exclusionReason=data.get("exclusionReason"),
            candidateUseCaseRefs=[str(item) for item in data.get("candidateUseCaseRefs", [])],
            priority=data.get("priority", "medium"),
        )

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class CandidateValidationUseCase:
    alias: str
    surface: str
    behavior: str
    sourceInventoryItems: list[str]
    rationale: str
    confidence: Literal["high", "medium", "low"] = "medium"
    inventorySourceStatus: Literal["complete", "partial", "stale"] = "partial"
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    requiresEnvironment: bool = False
    knownRuntimeRequirements: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any], inventory_status: str = "partial") -> "CandidateValidationUseCase":
        alias = str(data.get("alias") or data.get("candidateAlias") or "")
        surface = str(data.get("surface") or data.get("targetSurface") or "")
        source_items = data.get("sourceInventoryItems") or data.get("sourceCoverageItems") or data.get("sourceContext") or []
        return cls(
            alias=alias,
            surface=surface,
            behavior=str(data.get("behavior") or data.get("description") or data.get("title") or ""),
            sourceInventoryItems=[str(item) for item in source_items],
            rationale=str(data.get("rationale") or data.get("description") or data.get("behavior") or ""),
            confidence=data.get("confidence", "medium"),
            inventorySourceStatus=data.get("inventorySourceStatus", inventory_status),
            priority=data.get("priority", "medium"),
            requiresEnvironment=bool(data.get("requiresEnvironment", False)),
            knownRuntimeRequirements=[str(item) for item in data.get("knownRuntimeRequirements", [])],
        )

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class CoverageInventory:
    status: Literal["complete", "partial", "stale"] = "partial"
    generatedAt: str = ""
    generatedGitHash: str | None = None
    gitAvailable: bool = False
    passes: list[InventoryPass] = field(default_factory=list)
    items: list[CoverageInventoryItem] = field(default_factory=list)
    candidateUseCases: list[CandidateValidationUseCase] = field(default_factory=list)
    uncoveredAreas: list[str] = field(default_factory=list)
    staleAreas: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CoverageInventory":
        status = data.get("status", "partial")
        return cls(
            status=status,
            generatedAt=str(data.get("generatedAt", "")),
            generatedGitHash=data.get("generatedGitHash"),
            gitAvailable=bool(data.get("gitAvailable", False)),
            passes=[InventoryPass.from_dict(item) for item in data.get("passes", [])],
            items=[CoverageInventoryItem.from_dict(item) for item in data.get("items", [])],
            candidateUseCases=[CandidateValidationUseCase.from_dict(item, status) for item in data.get("candidateUseCases", [])],
            uncoveredAreas=[str(item) for item in data.get("uncoveredAreas", [])],
            staleAreas=[str(item) for item in data.get("staleAreas", [])],
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["passes"] = [item.to_dict() for item in self.passes]
        data["items"] = [item.to_dict() for item in self.items]
        data["candidateUseCases"] = [item.to_dict() for item in self.candidateUseCases]
        return clean(data)


@dataclass(slots=True)
class MigrationPlan:
    id: str
    reason: str
    affectedArtifacts: list[str]
    proposedActions: list[str]
    destructive: bool = False
    requiresApproval: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MigrationPlan":
        return cls(
            id=str(data.get("id", "")),
            reason=str(data.get("reason", "")),
            affectedArtifacts=[str(item) for item in data.get("affectedArtifacts", [])],
            proposedActions=[str(item) for item in data.get("proposedActions", [])],
            destructive=bool(data.get("destructive", False)),
            requiresApproval=bool(data.get("requiresApproval", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class StructuralWorkspaceValidation:
    status: Literal["pass", "warning", "blocked"] = "pass"
    findings: list[dict[str, Any]] = field(default_factory=list)
    checkedArtifacts: list[str] = field(default_factory=list)
    migrationPlans: list[MigrationPlan] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["migrationPlans"] = [item.to_dict() for item in self.migrationPlans]
        return clean(data)


@dataclass(slots=True)
class CoreReadiness:
    status: Literal["available", "missing", "incompatible", "error"] = "missing"
    coreCommand: str | None = None
    version: str | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class WorkflowCommand:
    canonicalName: str
    stage: str
    description: str
    argumentHint: str = ""
    sourceTemplate: str = ""
    integrationInvocation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class WorkflowDefinition:
    workflowId: str = WORKFLOW_ID
    name: str = "ProofSignal Use Case"
    version: str = "1.0.0"
    stages: list[str] = field(default_factory=lambda: WORKFLOW_STAGES.copy())
    gates: list[dict[str, Any]] = field(default_factory=list)
    defaultIntegration: str | None = None
    requiredInputs: list[str] = field(default_factory=lambda: ["goal", "alias"])

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowDefinition":
        return cls(
            workflowId=str(data.get("workflowId", WORKFLOW_ID)),
            name=str(data.get("name", "ProofSignal Use Case")),
            version=str(data.get("version", "1.0.0")),
            stages=[str(item.get("stage", item)) if isinstance(item, dict) else str(item) for item in data.get("stages", WORKFLOW_STAGES)],
            gates=list(data.get("gates", [])),
            defaultIntegration=data.get("defaultIntegration"),
            requiredInputs=list(data.get("requiredInputs", ["goal", "alias"])),
        )

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class WorkflowStageState:
    stage: str
    status: StageStatus = "pending"
    documentPath: str | None = None
    startedAt: str | None = None
    completedAt: str | None = None
    blockers: list[dict[str, Any]] = field(default_factory=list)
    nextCommand: str | None = None
    handoffSummary: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowStageState":
        return cls(
            stage=str(data.get("stage", "")),
            status=data.get("status", "pending"),
            documentPath=data.get("documentPath"),
            startedAt=data.get("startedAt"),
            completedAt=data.get("completedAt"),
            blockers=list(data.get("blockers", [])),
            nextCommand=data.get("nextCommand"),
            handoffSummary=data.get("handoffSummary"),
        )

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class WorkflowGateDecision:
    gateId: str
    stageBefore: str
    decision: GateDecisionValue
    decidedAt: str
    reason: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowGateDecision":
        return cls(
            gateId=str(data.get("gateId", "")),
            stageBefore=str(data.get("stageBefore", "")),
            decision=data.get("decision", "approved"),
            decidedAt=str(data.get("decidedAt", "")),
            reason=data.get("reason"),
        )

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class WorkflowRun:
    runId: str
    workflowId: str = WORKFLOW_ID
    useCaseAlias: str = ""
    integration: str | None = None
    status: WorkflowStatus = "paused"
    currentStage: str = "understand"
    startedAt: str | None = None
    updatedAt: str | None = None
    completedAt: str | None = None
    workflowDir: str | None = None
    stageStates: list[WorkflowStageState] = field(default_factory=list)
    gateDecisions: list[WorkflowGateDecision] = field(default_factory=list)
    nextCommand: str | None = None
    resumeCommand: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowRun":
        return cls(
            runId=str(data.get("runId", "")),
            workflowId=str(data.get("workflowId", WORKFLOW_ID)),
            useCaseAlias=str(data.get("useCaseAlias", "")),
            integration=data.get("integration"),
            status=data.get("status", "paused"),
            currentStage=str(data.get("currentStage", "understand")),
            startedAt=data.get("startedAt"),
            updatedAt=data.get("updatedAt"),
            completedAt=data.get("completedAt"),
            workflowDir=data.get("workflowDir"),
            stageStates=[WorkflowStageState.from_dict(item) for item in data.get("stageStates", [])],
            gateDecisions=[WorkflowGateDecision.from_dict(item) for item in data.get("gateDecisions", [])],
            nextCommand=data.get("nextCommand"),
            resumeCommand=data.get("resumeCommand"),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schemaVersion"] = WORKFLOW_RUN_SCHEMA
        data["stageStates"] = [item.to_dict() for item in self.stageStates]
        data["gateDecisions"] = [item.to_dict() for item in self.gateDecisions]
        return clean(data)


@dataclass(slots=True)
class UseCaseWorkflowReference:
    workflowDir: str
    currentStage: str
    workflowStatus: str
    lastWorkflowRunId: str | None = None
    lastUpdatedAt: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UseCaseWorkflowReference":
        return cls(
            workflowDir=str(data.get("workflowDir", "")),
            currentStage=str(data.get("currentStage", "understand")),
            workflowStatus=str(data.get("workflowStatus", "draft")),
            lastWorkflowRunId=data.get("lastWorkflowRunId"),
            lastUpdatedAt=data.get("lastUpdatedAt"),
        )

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class ArtifactPlan:
    useCaseAlias: str
    runRequest: str
    mainSkill: str
    supportingSkills: list[str] = field(default_factory=list)
    skillReuse: list[dict[str, Any]] = field(default_factory=list)
    runtimeInputs: list[dict[str, Any]] = field(default_factory=list)
    preconditions: list[str] = field(default_factory=list)
    validationGates: list[Any] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArtifactPlan":
        return cls(
            useCaseAlias=str(data.get("useCaseAlias", "")),
            runRequest=str(data.get("runRequest", "")),
            mainSkill=str(data.get("mainSkill", "")),
            supportingSkills=[str(item) for item in data.get("supportingSkills", [])],
            skillReuse=list(data.get("skillReuse", [])),
            runtimeInputs=list(data.get("runtimeInputs", [])),
            preconditions=[str(item) for item in data.get("preconditions", [])],
            validationGates=list(data.get("validationGates", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schemaVersion"] = WORKFLOW_ARTIFACT_PLAN_SCHEMA
        return clean(data)


@dataclass(slots=True)
class PlannedValidationGate:
    id: str
    description: str = ""
    required: bool = True
    condition: str | None = None
    conditionEvaluation: GateConditionEvaluation | None = None
    source: str = "plan.validationGates"
    legacy: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlannedValidationGate":
        gate_id = str(data.get("id") or data.get("gateId") or "").strip()
        return cls(
            id=gate_id,
            description=str(data.get("description") or data.get("title") or gate_id),
            required=bool(data.get("required", True)),
            condition=str(data.get("condition")).strip() if data.get("condition") else None,
            conditionEvaluation=data.get("conditionEvaluation"),
            source=str(data.get("source") or "plan.validationGates"),
            legacy=bool(data.get("legacy", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class RenderedResultAssertion:
    id: str
    gateId: str
    target: str
    kind: str
    expected: Any = None
    domainSemantics: str | None = None
    sourceArtifact: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class BackendRequestCheck:
    id: str
    gateId: str
    method: str | None = None
    urlContains: str | None = None
    operationName: str | None = None
    expectedStatus: int | str | None = None
    publicMatchKeys: list[str] = field(default_factory=list)
    sensitiveFieldsExcluded: bool = True
    sourceArtifact: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class ScreenshotEvidence:
    id: str
    gateId: str
    name: str | None = None
    sourceArtifact: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class EvidenceInventory:
    uiAssertions: list[RenderedResultAssertion] = field(default_factory=list)
    networkChecks: list[BackendRequestCheck] = field(default_factory=list)
    screenshots: list[ScreenshotEvidence] = field(default_factory=list)
    unmappedEvidence: list[dict[str, Any]] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["uiAssertions"] = [item.to_dict() for item in self.uiAssertions]
        data["networkChecks"] = [item.to_dict() for item in self.networkChecks]
        data["screenshots"] = [item.to_dict() for item in self.screenshots]
        return clean(data)


@dataclass(slots=True)
class GateCoverageResult:
    gateId: str
    status: GateCoverageStatus
    condition: str | None = None
    conditionEvaluation: GateConditionEvaluation | None = None
    uiEvidenceIds: list[str] = field(default_factory=list)
    networkEvidenceIds: list[str] = field(default_factory=list)
    screenshotEvidenceIds: list[str] = field(default_factory=list)
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class AuthoringCoherenceResult:
    alias: str
    status: Literal["passed", "warning", "blocked"] = "passed"
    mainSkill: str | None = None
    acceptedArtifactFields: list[str] = field(default_factory=lambda: ["path", "kind", "content", "intent", "browser"])
    normalizedAliases: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    gateCoverage: list[GateCoverageResult] = field(default_factory=list)
    schemaVersion: str = "proofsignal-spec-authoring-coherence/v1"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["gateCoverage"] = [item.to_dict() for item in self.gateCoverage]
        return clean(data)


@dataclass(slots=True)
class RuntimeContradiction:
    id: str
    gateId: str
    observedEvidence: str
    expectedEvidence: str
    recommendation: Literal["update-target-data", "mark-conditional", "replan"]
    sourceRunId: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class AuthoringTask:
    id: str
    description: str
    artifact: str | None = None
    status: str = "pending"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuthoringTask":
        return cls(
            id=str(data.get("id", "")),
            description=str(data.get("description", "")),
            artifact=data.get("artifact"),
            status=str(data.get("status", "pending")),
        )

    def to_dict(self) -> dict[str, Any]:
        return clean(asdict(self))


@dataclass(slots=True)
class AuthoringTaskSet:
    taskSetId: str
    useCaseAlias: str
    sourcePlanPath: str
    planFingerprint: str
    generatedAt: str
    tasks: list[AuthoringTask] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuthoringTaskSet":
        return cls(
            taskSetId=str(data.get("taskSetId", "")),
            useCaseAlias=str(data.get("useCaseAlias", "")),
            sourcePlanPath=str(data.get("sourcePlanPath", "")),
            planFingerprint=str(data.get("planFingerprint", "")),
            generatedAt=str(data.get("generatedAt", "")),
            tasks=[AuthoringTask.from_dict(item) for item in data.get("tasks", [])],
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schemaVersion"] = WORKFLOW_TASK_SET_SCHEMA
        data["tasks"] = [item.to_dict() for item in self.tasks]
        return clean(data)


def native_invocation(stage: str, style: str = "skill") -> str:
    separator = "-" if style == "skill" else "."
    return f"/proofsignal{separator}{stage}"
