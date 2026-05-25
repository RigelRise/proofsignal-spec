from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


WorkflowStatus = Literal["not-started", "running", "paused", "blocked", "failed", "completed"]
StageStatus = Literal["pending", "running", "completed", "blocked", "skipped", "failed"]
GateDecisionValue = Literal["approved", "rejected"]

WORKFLOW_ID = "proofsignal-use-case"
WORKFLOW_RUN_SCHEMA = "proofsignal-spec-workflow-run/v1"
WORKFLOW_STATE_SCHEMA = "proofsignal-spec-workflow-state/v1"
WORKFLOW_TASK_SET_SCHEMA = "proofsignal-spec-workflow-tasks/v1"
WORKFLOW_ARTIFACT_PLAN_SCHEMA = "proofsignal-spec-workflow-artifact-plan/v1"
WORKFLOW_PREREQUISITE_CHECK_SCHEMA = "proofsignal-spec-workflow-prerequisite-check/v1"
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
    validationGates: list[str] = field(default_factory=list)

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
            validationGates=[str(item) for item in data.get("validationGates", [])],
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schemaVersion"] = WORKFLOW_ARTIFACT_PLAN_SCHEMA
        return clean(data)


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
