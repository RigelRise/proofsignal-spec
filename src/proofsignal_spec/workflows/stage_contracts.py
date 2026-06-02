from __future__ import annotations

from typing import Any

from .models import StagePayloadValidationFinding, WorkflowStageContract


STAGE_CONTRACTS_SCHEMA = "proofsignal-spec-stage-payload-contracts/v1"

_STAGE_CONTRACTS: dict[str, WorkflowStageContract] = {
    "specify": WorkflowStageContract(
        stage="specify",
        requiredFields=["surface", "behavior", "expectedOutcome"],
        optionalFields=[
            "alias",
            "title",
            "sourceInventoryItems",
            "customSourceReason",
            "runtimeAssumptions",
            "targetEnvironment",
            "targetSurface",
            "purpose",
            "description",
            "expectedOutcomes",
        ],
        defaults={"status": "draft"},
        examples=[
            {
                "alias": "home-page-unauth",
                "surface": "/",
                "behavior": "Validate the public home page.",
                "expectedOutcome": "Hero, activity, Teams, and Brands sections render.",
                "targetEnvironment": {"kind": "staging-url", "locator": "https://app.example.test"},
                "customSourceReason": "Selected by developer.",
            }
        ],
        nextAction="proofsignal workflow persist specify --alias <alias> --payload <payload.json> --json",
    ),
    "clarify": WorkflowStageContract(
        stage="clarify",
        requiredFields=["questions or answers"],
        optionalFields=["alias", "questions", "answers"],
        examples=[
            {
                "questions": [
                    {
                        "id": "target-environment",
                        "prompt": "Which target environment should be used?",
                        "affects": "runtime",
                        "status": "answered",
                        "answerSummary": "https://app.example.test",
                    }
                ]
            }
        ],
        nextAction="proofsignal workflow persist clarify --alias <alias> --payload <payload.json> --json",
    ),
    "plan": WorkflowStageContract(
        stage="plan",
        requiredFields=["runRequest", "reusableSkills", "runtimeInputs"],
        optionalFields=[
            "alias",
            "mainSkill",
            "supportingSkills",
            "skills",
            "skillReuse",
            "preconditions",
            "validationGates",
            "gateIntentChanges",
            "credentialGroups",
            "targetEnvironment",
            "unresolvedBlockingClarifications",
        ],
        defaults={"runRequest": ".proofsignal/run-requests/<alias>.yaml", "runtimeInputs": []},
        examples=[
            {
                "runRequest": ".proofsignal/run-requests/home-page-unauth.yaml",
                "mainSkill": ".proofsignal/skills/validate-home-page-unauth-flow.browser.md",
                "reusableSkills": [".proofsignal/skills/validate-home-page-unauth-flow.browser.md"],
                "runtimeInputs": [{"name": "baseUrl", "value": "https://app.example.test"}],
                "validationGates": [{"id": "home-hero-visible", "required": True}],
            }
        ],
        nextAction="proofsignal workflow persist plan --alias <alias> --payload <payload.json> --json",
    ),
    "tasks": WorkflowStageContract(
        stage="tasks",
        requiredFields=["tasks"],
        optionalFields=["alias", "dependencies", "parallelizableGroups"],
        examples=[
            {
                "tasks": [
                    {
                        "id": "T001",
                        "description": "Author the browser skill target map.",
                        "artifact": ".proofsignal/skills/validate-home-page-unauth-flow.browser.md",
                    }
                ]
            }
        ],
        nextAction="proofsignal workflow persist tasks --alias <alias> --payload <payload.json> --json",
    ),
    "implement": WorkflowStageContract(
        stage="implement",
        requiredFields=["runRequest", "skills"],
        optionalFields=["alias", "runtimeInputs", "profiles", "artifacts", "credentialGroups"],
        examples=[
            {
                "runRequest": {"path": ".proofsignal/run-requests/home-page-unauth.yaml"},
                "runtimeInputs": [{"name": "baseUrl", "value": "https://app.example.test"}],
                "skills": [
                    {
                        "path": ".proofsignal/skills/validate-home-page-unauth-flow.browser.md",
                        "kind": "skill",
                        "intent": {
                            "browser": {
                                "targets": {"page": {"css": "body"}},
                                "steps": [{"id": "open", "action": "navigate", "value": "{{parameters.baseUrl}}/"}],
                                "assertions": [{"id": "page-visible", "kind": "visible", "target": "page", "gateId": "home-hero-visible"}],
                            }
                        },
                    }
                ],
            }
        ],
        nextAction="proofsignal workflow persist implement --alias <alias> --payload <payload.json> --json",
    ),
}

_ALIASES: dict[str, set[str]] = {
    "specify": {"route", "targetSurface", "purpose", "description", "intent", "expectedOutcomes", "baseUrl", "targetUrl", "url", "stagingUrl", "environmentUrl"},
    "plan": {"skills", "supportingSkills", "mainSkill"},
    "implement": {"artifacts"},
}


class StagePayloadContractError(ValueError):
    def __init__(self, finding: StagePayloadValidationFinding) -> None:
        super().__init__(finding.message)
        self.finding = finding


def stage_contract(stage: str) -> WorkflowStageContract | None:
    return _STAGE_CONTRACTS.get(stage)


def stage_contracts_payload() -> dict[str, Any]:
    contracts = {stage: contract.to_dict() for stage, contract in _STAGE_CONTRACTS.items()}
    return {
        "schemaVersion": STAGE_CONTRACTS_SCHEMA,
        "stages": list(_STAGE_CONTRACTS),
        "byStage": contracts,
        "guidance": "Use these public workflow contracts; do not inspect installed package source to infer payload schemas.",
    }


def unsupported_field_warnings(stage: str, payload: dict[str, Any]) -> list[str]:
    contract = stage_contract(stage)
    if not contract:
        return []
    allowed = {"payload", *contract.requiredFields, *contract.optionalFields, *(_ALIASES.get(stage, set()))}
    warnings: list[str] = []
    for key in payload:
        if key not in allowed:
            warnings.append(
                f"Unsupported field '{key}' is not part of stagePayloadContracts.{stage}. "
                f"Review `proofsignal workflow info proofsignal-use-case --json` before persisting this stage."
            )
    return warnings


def missing_required_field_error(stage: str, field: str) -> StagePayloadContractError:
    finding = StagePayloadValidationFinding(
        id=f"{stage}.{field}.missing",
        stage=stage,
        fieldPath=field,
        severity="blocked",
        message=f"Payload missing required public contract field '{field}' for stage '{stage}'.",
        expectedContract=f"stagePayloadContracts.{stage}.requiredFields.{field}",
        recoveryAction="Run `proofsignal workflow info proofsignal-use-case --json` and submit the documented stage payload shape.",
    )
    return StagePayloadContractError(finding)
