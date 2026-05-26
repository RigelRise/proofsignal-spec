from __future__ import annotations

from proofsignal_spec.workspace.repository import create_default_use_case, init_workspace, load_use_case, save_use_case
from proofsignal_spec.workflows.repository import import_legacy_use_case
from proofsignal_spec.workflows.migration import apply_migration
from tests.fixtures.workflows.guardrails import create_registry_missing_record_path


def test_legacy_use_case_imports_as_workflow_draft(tmp_path) -> None:
    init_workspace(tmp_path)
    save_use_case(tmp_path, create_default_use_case(tmp_path, "login", "Validate login."))
    result = import_legacy_use_case(tmp_path, "login")
    assert result["alias"] == "login"
    assert load_use_case(tmp_path, "login").workflow is not None


def test_recoverable_legacy_registry_entry_upgrades_to_use_case_record(tmp_path) -> None:
    create_registry_missing_record_path(tmp_path, "legacy-login")
    result = apply_migration(tmp_path, "migrate-registry-record-path-legacy-login")
    assert result["status"] == "applied"
    assert load_use_case(tmp_path, "legacy-login").alias == "legacy-login"
