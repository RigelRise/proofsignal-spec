from __future__ import annotations

from verifysignal_spec.workflows.readiness import default_capability_policies
from verifysignal_spec.workspace.repository import load_use_case, run_confirmation_requirements
from tests.fixtures.workflows.live_write_readiness import create_live_write_readiness_workspace


def test_default_capability_policy_marks_write_safety_capabilities_as_confirmation_or_warning() -> None:
    policies = {policy.capability: policy for policy in default_capability_policies()}

    assert policies["explicit-confirmation"].severityWhenMissing == "confirmation"
    assert policies["side-effect-lifecycle"].safetyCritical is True
    assert policies["generated-runtime-inputs"].migrationGuidance


def test_legacy_write_use_case_missing_capabilities_requires_confirmation(tmp_path) -> None:
    create_live_write_readiness_workspace(tmp_path)
    record = load_use_case(tmp_path, "add-collaboration-project")

    requirements = run_confirmation_requirements(tmp_path, record)

    assert any(item.scope == "legacy-missing-safety-capability" for item in requirements)
    assert any("explicit-confirmation" in item.reason for item in requirements)
