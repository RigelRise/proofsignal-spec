from __future__ import annotations

from proofsignal_spec.workspace.repository import capability_stamp, load_use_case, run_confirmation_requirements, save_use_case
from tests.fixtures.workflows.live_write_readiness import create_live_write_readiness_workspace


def test_current_capability_stamp_satisfies_legacy_missing_capability_confirmation(tmp_path) -> None:
    create_live_write_readiness_workspace(tmp_path)
    record = load_use_case(tmp_path, "add-collaboration-project")
    record.sideEffectLifecycle = {"cleanupPolicy": "manual", "cleanupRequired": True, "instructions": "Delete created project manually."}
    record.artifactCapabilities = {
        "status": "current",
        "stamp": capability_stamp(
            ["explicit-confirmation", "side-effect-lifecycle", "write-activity-interpretation"],
            contract_version="proofsignal-spec-use-case/v1",
        ),
    }
    save_use_case(tmp_path, record)

    requirements = run_confirmation_requirements(tmp_path, load_use_case(tmp_path, "add-collaboration-project"))

    assert not any(item.scope == "legacy-missing-safety-capability" for item in requirements)
    assert not any(item.scope == "missing-side-effect-lifecycle" for item in requirements)
