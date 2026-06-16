from __future__ import annotations

from proofsignal_spec.commands.list import run as list_run
from tests.fixtures.workflows.live_write_readiness import create_live_write_readiness_workspace, old_checked_at, save_ready_snapshot
from tests.helpers import row_by_alias


def test_list_rows_are_compact_and_do_not_claim_current_ready_without_snapshot(tmp_path) -> None:
    create_live_write_readiness_workspace(tmp_path)

    payload = list_run(tmp_path)

    public = row_by_alias(payload, "about-page-unauth")
    credentialed = row_by_alias(payload, "brands-search-authenticated")
    write = row_by_alias(payload, "add-collaboration-project")
    assert public["lastRun"]["status"] == "passed"
    assert public["current"]["status"] == "not-checked"
    assert credentialed["current"]["status"] == "not-checked"
    assert write["current"]["status"] == "not-checked"
    assert set(write["requirements"]) == {"runtimeInputs", "credentials", "sideEffectClass", "cleanupPolicy"}
    assert set(write["risk"]).issuperset({"classes", "write", "cleanupPolicy", "requiresConfirmation"})


def test_list_applies_risk_based_snapshot_age(tmp_path) -> None:
    create_live_write_readiness_workspace(tmp_path)
    save_ready_snapshot(tmp_path, "about-page-unauth", checked_at=old_checked_at(days=6))
    save_ready_snapshot(tmp_path, "add-collaboration-project", checked_at=old_checked_at(hours=25), side_effect_class="write")

    payload = list_run(tmp_path)

    assert row_by_alias(payload, "about-page-unauth")["current"]["status"] == "ready"
    assert row_by_alias(payload, "add-collaboration-project")["current"]["status"] == "stale"


def test_list_does_not_call_core_or_credential_runtime(tmp_path, monkeypatch) -> None:
    create_live_write_readiness_workspace(tmp_path)

    def fail(*_args, **_kwargs):
        raise AssertionError("list must not perform Core runtime checks")

    monkeypatch.setattr("proofsignal_spec.runtime.resolver.ensure_core_runtime", fail)
    monkeypatch.setenv("APP_TEST_EMAIL", "secret@example.test")
    monkeypatch.delenv("APP_TEST_PASSWORD", raising=False)

    payload = list_run(tmp_path)

    assert row_by_alias(payload, "brands-search-authenticated")["requirements"]["credentials"][0]["runtimeNames"] == [
        "APP_TEST_EMAIL",
        "APP_TEST_PASSWORD",
    ]
    assert "secret@example.test" not in str(payload)
