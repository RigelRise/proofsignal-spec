from __future__ import annotations

from proofsignal_spec.workflows.migration import apply_migration, migration_plans

from tests.fixtures.workflows.guardrails import create_registry_missing_record_path


def test_missing_record_path_migration_plan_is_recoverable(tmp_path) -> None:
    project = tmp_path / "repo"
    project.mkdir()
    create_registry_missing_record_path(project, "login")
    plans = migration_plans(project)
    assert plans[0].id == "migrate-registry-record-path-login"
    assert not plans[0].destructive


def test_apply_migration_creates_canonical_use_case_record(tmp_path) -> None:
    project = tmp_path / "repo"
    project.mkdir()
    create_registry_missing_record_path(project, "login")
    result = apply_migration(project, "migrate-registry-record-path-login")
    assert result["status"] == "applied"
    assert (project / ".proofsignal/use-cases/login.yaml").exists()
