from __future__ import annotations

import os

from helpers import FAKE_CORE
from verifysignal_spec.core.adapter import CoreAdapter
from verifysignal_spec.core.executable_contract import project_core_contract
from verifysignal_spec.workspace.models import ArtifactReference, UseCaseRecord
from verifysignal_spec.workflows.authoring_coherence import evaluate_implementation_coherence
from verifysignal_spec.workflows.models import ArtifactPlan
from verifysignal_spec.workflows.repository import save_artifact_plan
from verifysignal_spec.workflows.skill_execution_boundary import multi_skill_capability, resolve_execution_boundary
from tests.fixtures.workflows.skill_execution_boundary import ALIAS, LOGIN_SKILL_PATH, MAIN_SKILL_PATH, login_browser, main_browser


def _projected_contract(mode: str | None = None) -> dict[str, object]:
    old_mode = os.environ.get("FAKE_VERIFYSIGNAL_MODE")
    if mode:
        os.environ["FAKE_VERIFYSIGNAL_MODE"] = mode
    else:
        os.environ.pop("FAKE_VERIFYSIGNAL_MODE", None)
    try:
        return project_core_contract(CoreAdapter(executable=str(FAKE_CORE)).contracts())
    finally:
        if old_mode is None:
            os.environ.pop("FAKE_VERIFYSIGNAL_MODE", None)
        else:
            os.environ["FAKE_VERIFYSIGNAL_MODE"] = old_mode


def _record() -> UseCaseRecord:
    main = ArtifactReference(path=".verifysignal/skills/main.browser.md", kind="skill", id="skill.main")
    helper = ArtifactReference(path=".verifysignal/skills/login.browser.md", kind="skill", id="skill.login")
    return UseCaseRecord(
        alias="auth-brands",
        title="Auth Brands",
        description="Validate authenticated brands.",
        runRequest=ArtifactReference(path=".verifysignal/run-requests/auth-brands.yaml", kind="run-request"),
        mainSkill=main,
        skills=[main, helper],
        sourceOnlySkills=[helper],
    )


def test_multiple_unsupported_resolves_single_main_and_excludes_source_only_helper() -> None:
    decision = resolve_execution_boundary(_record(), core_contract=_projected_contract())

    assert decision.mode == "single-main"
    assert [item.id for item in decision.executableSkills] == ["skill.main"]
    assert [item.id for item in decision.sourceOnlySkills] == ["skill.login"]


def test_reusable_marked_executable_legacy_run_request_blocks_when_unclassified() -> None:
    record = _record()
    record.sourceOnlySkills = []

    decision = resolve_execution_boundary(
        record,
        core_contract=_projected_contract(),
        run_request={"skills": [{"id": "skill.login"}, {"id": "skill.main"}]},
    )

    assert any(item["code"] == "skill-execution.legacy-migration-required" for item in decision.findings)


def test_multiple_authored_executable_skills_block_when_core_is_unsupported() -> None:
    record = _record()
    record.sourceOnlySkills = []

    decision = resolve_execution_boundary(record, core_contract=_projected_contract())

    assert any(item["code"] == "skill-execution.multiple-unsupported" for item in decision.findings)


def test_source_only_skill_in_run_request_blocks_as_reusable_marked_executable() -> None:
    decision = resolve_execution_boundary(
        _record(),
        core_contract=_projected_contract(),
        run_request={"skills": [{"id": "skill.main"}, {"id": "skill.login"}]},
    )

    assert any(item["code"] == "skill-execution.reusable-marked-executable" for item in decision.findings)


def test_supported_multi_skill_contract_declares_roles_ordering_and_evidence_semantics() -> None:
    capability = multi_skill_capability(_projected_contract("multi-skill-supported"))

    assert capability.supported is True
    assert capability.mode == "core-declared-multi-skill"
    assert capability.roles == ["main", "precondition"]
    assert capability.ordering == "declared-list-order"
    assert capability.evidenceSemantics == "gateId-attributed-per-participant"


def test_supported_multi_skill_contract_preserves_explicit_source_only_skills() -> None:
    decision = resolve_execution_boundary(_record(), core_contract=_projected_contract("multi-skill-supported"))

    assert [item.id for item in decision.executableSkills] == ["skill.main"]
    assert [item.id for item in decision.sourceOnlySkills] == ["skill.login"]


def test_partial_support_falls_back_to_single_main_for_browser_helpers() -> None:
    capability = multi_skill_capability(_projected_contract("partial-skill-support"))
    decision = resolve_execution_boundary(_record(), core_contract=_projected_contract("partial-skill-support"))

    assert capability.supported is False
    assert capability.mode == "partial-support"
    assert "precondition" in capability.partialExecutableRoles
    assert [item.id for item in decision.executableSkills] == ["skill.main"]


def test_gate_evidence_requires_mapping_for_source_only_skill(tmp_path) -> None:
    save_artifact_plan(
        tmp_path,
        ArtifactPlan(
            useCaseAlias=ALIAS,
            runRequest=f".verifysignal/run-requests/{ALIAS}.yaml",
            mainSkill=MAIN_SKILL_PATH,
            supportingSkills=[LOGIN_SKILL_PATH],
            sourceOnlySkills=[LOGIN_SKILL_PATH],
            validationGates=[{"id": "login-succeeds", "required": True, "description": "Login succeeds"}],
        ),
    )
    main = main_browser(include_login=False)
    main["assertions"] = [item for item in main["assertions"] if item.get("gateId") != "login-succeeds"]

    result = evaluate_implementation_coherence(
        tmp_path,
        ALIAS,
        {
            "skills": [
                {"path": MAIN_SKILL_PATH, "browser": main},
                {"path": LOGIN_SKILL_PATH, "browser": login_browser()},
            ]
        },
    )

    assert result.status == "blocked"
    assert any(item.gateId == "login-succeeds" and item.status == "missing" for item in result.gateCoverage)
