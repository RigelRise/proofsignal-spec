from __future__ import annotations

from dataclasses import asdict, field
from typing import Any, Literal

try:  # Pydantic-backed dataclasses when the planned dependency is installed.
    from pydantic.dataclasses import dataclass
except Exception:  # pragma: no cover - fallback for minimal bootstrap envs
    from dataclasses import dataclass


Status = Literal["draft", "ready", "blocked", "failed", "deprecated", "unknown"]
CoreStatus = Literal["passed", "failed", "blocked", "error"]


def _clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_clean(v) for v in value]
    return value


@dataclass(slots=True)
class ArtifactReference:
    path: str
    kind: Literal["run-request", "skill", "external"]
    generated: bool = True
    id: str | None = None
    version: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArtifactReference":
        return cls(
            path=str(data.get("path", "")),
            kind=data.get("kind", "external"),
            generated=bool(data.get("generated", False)),
            id=data.get("id"),
            version=data.get("version"),
        )

    def to_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass(slots=True)
class RuntimeInputRequirement:
    name: str
    kind: Literal["parameter", "credential", "precondition-input"] = "parameter"
    required: bool = True
    description: str = ""
    source: Literal["prompt", "environment", "local-config", "default"] = "prompt"
    envVar: str | None = None
    credentialGroup: str | None = None
    persistValue: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RuntimeInputRequirement":
        return cls(
            name=str(data.get("name", "")),
            kind=data.get("kind", "parameter"),
            required=bool(data.get("required", True)),
            description=str(data.get("description", "")),
            source=data.get("source", "prompt"),
            envVar=data.get("envVar"),
            credentialGroup=data.get("credentialGroup"),
            persistValue=bool(data.get("persistValue", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass(slots=True)
class RunProfile:
    name: str = "normal"
    description: str = ""
    headed: bool = False
    slowMoMs: int = 0
    outputDir: str | None = None
    assumePreconditionsReady: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunProfile":
        return cls(
            name=str(data.get("name", "normal")),
            description=str(data.get("description", "")),
            headed=bool(data.get("headed", False)),
            slowMoMs=int(data.get("slowMoMs", 0) or 0),
            outputDir=data.get("outputDir"),
            assumePreconditionsReady=bool(data.get("assumePreconditionsReady", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass(slots=True)
class AuthoringQuestion:
    id: str
    prompt: str
    reason: str = ""
    status: Literal["pending", "answered", "deferred"] = "pending"
    answerSummary: str | None = None
    affects: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuthoringQuestion":
        return cls(
            id=str(data.get("id", "")),
            prompt=str(data.get("prompt", "")),
            reason=str(data.get("reason", "")),
            status=data.get("status", "pending"),
            answerSummary=data.get("answerSummary"),
            affects=data.get("affects"),
        )

    def to_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass(slots=True)
class RunHistoryEntry:
    runId: str
    useCaseAlias: str
    profile: str
    status: str
    startedAt: str
    completedAt: str | None = None
    coreStatus: str | None = None
    coverageStatus: str | None = None
    profileSettings: dict[str, Any] | None = None
    selectedMainSkill: dict[str, Any] | str | None = None
    executedSkill: dict[str, Any] | str | None = None
    skillSelectionStatus: str | None = None
    gateCoverage: list[dict[str, Any]] = field(default_factory=list)
    missingRequiredGates: list[str] = field(default_factory=list)
    partialCoverage: list[dict[str, Any]] = field(default_factory=list)
    runtimeContradictions: list[dict[str, Any]] = field(default_factory=list)
    repairRecommendations: list[dict[str, Any]] = field(default_factory=list)
    summary: str | dict[str, Any] | None = None
    reportPath: str | None = None
    evidenceDir: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunHistoryEntry":
        return cls(
            runId=str(data.get("runId", "")),
            useCaseAlias=str(data.get("useCaseAlias", "")),
            profile=str(data.get("profile", "normal")),
            status=data.get("status", "error"),
            startedAt=str(data.get("startedAt", "")),
            completedAt=data.get("completedAt"),
            coreStatus=data.get("coreStatus"),
            coverageStatus=data.get("coverageStatus"),
            profileSettings=data.get("profileSettings"),
            selectedMainSkill=data.get("selectedMainSkill"),
            executedSkill=data.get("executedSkill"),
            skillSelectionStatus=data.get("skillSelectionStatus"),
            gateCoverage=list(data.get("gateCoverage", [])),
            missingRequiredGates=[str(item) for item in data.get("missingRequiredGates", [])],
            partialCoverage=list(data.get("partialCoverage", [])),
            runtimeContradictions=list(data.get("runtimeContradictions", [])),
            repairRecommendations=list(data.get("repairRecommendations", [])),
            summary=data.get("summary"),
            reportPath=data.get("reportPath"),
            evidenceDir=data.get("evidenceDir"),
        )

    def to_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass(slots=True)
class RepairSession:
    repairId: str
    useCaseAlias: str
    source: Literal["authoring-validation", "report-inspection"]
    findings: list[dict[str, Any]] = field(default_factory=list)
    proposals: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    repairConfirmations: list[dict[str, Any]] = field(default_factory=list)
    applications: list[dict[str, Any]] = field(default_factory=list)
    repairFeedback: list[dict[str, Any]] = field(default_factory=list)
    stageCards: list[dict[str, Any]] = field(default_factory=list)
    approvalStatus: Literal["pending", "approved", "rejected", "conflict", "applied"] = "pending"
    appliedAt: str | None = None
    revalidation: dict[str, Any] | None = None
    readyForRun: bool = False
    nextAction: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RepairSession":
        return cls(
            repairId=str(data.get("repairId", "")),
            useCaseAlias=str(data.get("useCaseAlias", "")),
            source=data.get("source", "authoring-validation"),
            findings=list(data.get("findings", [])),
            proposals=list(data.get("proposals", [])),
            recommendations=list(data.get("recommendations", [])),
            repairConfirmations=list(data.get("repairConfirmations", [])),
            applications=list(data.get("applications", [])),
            repairFeedback=list(data.get("repairFeedback", [])),
            stageCards=list(data.get("stageCards", [])),
            approvalStatus=data.get("approvalStatus", "pending"),
            appliedAt=data.get("appliedAt"),
            revalidation=data.get("revalidation"),
            readyForRun=bool(data.get("readyForRun", False)),
            nextAction=data.get("nextAction"),
        )

    def to_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass(slots=True)
class UseCaseRecord:
    alias: str
    title: str
    description: str
    targetSurface: str = "browser"
    status: Status = "draft"
    runRequest: ArtifactReference | None = None
    mainSkill: ArtifactReference | None = None
    skills: list[ArtifactReference] = field(default_factory=list)
    runtimeInputs: list[RuntimeInputRequirement] = field(default_factory=list)
    credentialRefs: dict[str, Any] = field(default_factory=dict)
    credentialGroups: list[dict[str, Any] | str] = field(default_factory=list)
    profiles: list[RunProfile] = field(
        default_factory=lambda: [
            RunProfile(),
            RunProfile(name="debug", description="Visible browser debug profile", headed=True, slowMoMs=900),
            RunProfile(name="browser", description="Visible browser profile", headed=True, slowMoMs=900),
        ]
    )
    authoringQuestions: list[AuthoringQuestion] = field(default_factory=list)
    validation: dict[str, Any] = field(default_factory=lambda: {"status": "unknown"})
    lastRun: dict[str, Any] | None = None
    repair: dict[str, Any] | None = None
    workflow: dict[str, Any] | None = None
    schemaVersion: str = "proofsignal-spec-use-case/v1"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UseCaseRecord":
        return cls(
            schemaVersion=str(data.get("schemaVersion", "proofsignal-spec-use-case/v1")),
            alias=str(data.get("alias", "")),
            title=str(data.get("title", "")),
            description=str(data.get("description", "")),
            targetSurface=str(data.get("targetSurface", "browser")),
            status=data.get("status", "draft"),
            runRequest=ArtifactReference.from_dict(data["runRequest"]) if data.get("runRequest") else None,
            mainSkill=ArtifactReference.from_dict(data["mainSkill"]) if data.get("mainSkill") else None,
            skills=[ArtifactReference.from_dict(item) for item in data.get("skills", [])],
            runtimeInputs=[RuntimeInputRequirement.from_dict(item) for item in data.get("runtimeInputs", [])],
            credentialRefs=dict(data.get("credentialRefs", {})),
            credentialGroups=list(data.get("credentialGroups", [])),
            profiles=[RunProfile.from_dict(item) for item in data.get("profiles", [])] or [RunProfile()],
            authoringQuestions=[AuthoringQuestion.from_dict(item) for item in data.get("authoringQuestions", [])],
            validation=dict(data.get("validation", {"status": "unknown"})),
            lastRun=data.get("lastRun"),
            repair=data.get("repair"),
            workflow=data.get("workflow"),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["runRequest"] = self.runRequest.to_dict() if self.runRequest else None
        data["mainSkill"] = self.mainSkill.to_dict() if self.mainSkill else None
        data["skills"] = [item.to_dict() for item in self.skills]
        data["runtimeInputs"] = [item.to_dict() for item in self.runtimeInputs]
        data["credentialRefs"] = dict(self.credentialRefs)
        data["profiles"] = [item.to_dict() for item in self.profiles]
        data["authoringQuestions"] = [item.to_dict() for item in self.authoringQuestions]
        return _clean(data)


@dataclass(slots=True)
class ManagedFileRecord:
    path: str
    sha256: str
    source: str
    kind: Literal["agent-skill", "context", "workspace-template", "manifest", "onboarding-guide"]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ManagedFileRecord":
        return cls(path=str(data.get("path", "")), sha256=str(data.get("sha256", "")), source=str(data.get("source", "")), kind=data.get("kind", "agent-skill"))

    def to_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass(slots=True)
class AgentIntegrationState:
    key: str
    displayName: str
    installedAt: str
    default: bool = False
    managedFiles: list[ManagedFileRecord] = field(default_factory=list)
    invokeStyle: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentIntegrationState":
        return cls(
            key=str(data.get("key", "")),
            displayName=str(data.get("displayName", "")),
            installedAt=str(data.get("installedAt", "")),
            default=bool(data.get("default", False)),
            managedFiles=[ManagedFileRecord.from_dict(item) for item in data.get("managedFiles", [])],
            invokeStyle=str(data.get("invokeStyle", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["managedFiles"] = [item.to_dict() for item in self.managedFiles]
        return _clean(data)
