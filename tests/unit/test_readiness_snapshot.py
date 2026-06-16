from __future__ import annotations

from proofsignal_spec.workspace.repository import load_use_case, readiness_current_state
from tests.fixtures.workflows.live_write_readiness import (
    create_live_write_readiness_workspace,
    old_checked_at,
    save_ready_snapshot,
)


def test_no_snapshot_is_not_current_ready_even_when_last_run_passed(tmp_path) -> None:
    create_live_write_readiness_workspace(tmp_path)
    record = load_use_case(tmp_path, "add-collaboration-project")

    current = readiness_current_state(tmp_path, record)

    assert current["status"] == "not-checked"
    assert current["lastRunStatus"] == "passed"
    assert current["checked"] is False


def test_public_read_only_snapshot_under_seven_days_stays_ready(tmp_path) -> None:
    create_live_write_readiness_workspace(tmp_path)
    save_ready_snapshot(tmp_path, "about-page-unauth", checked_at=old_checked_at(days=6), side_effect_class="none")
    record = load_use_case(tmp_path, "about-page-unauth")

    current = readiness_current_state(tmp_path, record)

    assert current["status"] == "ready"
    assert current["checked"] is True


def test_write_snapshot_older_than_twenty_four_hours_needs_validation(tmp_path) -> None:
    create_live_write_readiness_workspace(tmp_path)
    save_ready_snapshot(tmp_path, "add-collaboration-project", checked_at=old_checked_at(hours=25), side_effect_class="write")
    record = load_use_case(tmp_path, "add-collaboration-project")

    current = readiness_current_state(tmp_path, record)

    assert current["status"] == "stale"
    assert any(item["code"] == "age-expired" for item in current["invalidationReasons"])


def test_artifact_change_invalidates_snapshot(tmp_path) -> None:
    create_live_write_readiness_workspace(tmp_path)
    save_ready_snapshot(tmp_path, "about-page-unauth")
    (tmp_path / ".proofsignal/skills/about-page-unauth.browser.md").write_text("changed", encoding="utf-8")
    record = load_use_case(tmp_path, "about-page-unauth")

    current = readiness_current_state(tmp_path, record)

    assert current["status"] == "stale"
    assert any(item["code"] == "artifact-changed" for item in current["invalidationReasons"])
