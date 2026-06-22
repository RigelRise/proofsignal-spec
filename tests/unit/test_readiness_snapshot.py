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


def test_committed_write_surfaces_rerun_confirmation_not_stale(tmp_path) -> None:
    # Issue 5: a committed write must surface as 'needs-rerun-confirmation' (cleared by
    # supersede/approve), NOT 'stale — Needs validation' (which validate cannot clear).
    from proofsignal_spec.workspace.repository import save_use_case
    from tests.fixtures.workflows.side_effect_contract_alignment import confirmable_write_last_run

    create_live_write_readiness_workspace(tmp_path)
    save_ready_snapshot(tmp_path, "add-collaboration-project", side_effect_class="write")

    record = load_use_case(tmp_path, "add-collaboration-project")
    record.lastRun = confirmable_write_last_run(run_id="add-collaboration-project-20260622T202124Z")
    save_use_case(tmp_path, record)

    current = readiness_current_state(tmp_path, load_use_case(tmp_path, "add-collaboration-project"))

    assert current["status"] == "needs-rerun-confirmation", current
    assert any(item["code"] == "write-post-commit-risk" for item in current["invalidationReasons"])
    assert "validate" not in (current.get("nextAction") or "")


def test_committed_write_with_freshness_drift_stays_stale(tmp_path) -> None:
    # When BOTH a freshness reason (age-expired) and the write-rerun guard are present,
    # freshness wins (validate first), so the status remains 'stale'.
    from proofsignal_spec.workspace.repository import save_use_case
    from tests.fixtures.workflows.side_effect_contract_alignment import confirmable_write_last_run

    create_live_write_readiness_workspace(tmp_path)
    save_ready_snapshot(tmp_path, "add-collaboration-project", checked_at=old_checked_at(hours=25), side_effect_class="write")

    record = load_use_case(tmp_path, "add-collaboration-project")
    record.lastRun = confirmable_write_last_run()
    save_use_case(tmp_path, record)

    current = readiness_current_state(tmp_path, load_use_case(tmp_path, "add-collaboration-project"))

    assert current["status"] == "stale", current


def _save_snapshot_with_spec_version(tmp_path, alias: str, spec_version: str) -> None:
    from datetime import UTC, datetime

    from proofsignal_spec.workspace.models import ReadinessSnapshot
    from proofsignal_spec.workspace.repository import artifact_fingerprints, save_readiness_snapshot

    record = load_use_case(tmp_path, alias)
    save_readiness_snapshot(
        tmp_path,
        ReadinessSnapshot(
            alias=alias,
            status="ready",
            checkedAt=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            artifactFingerprints=artifact_fingerprints(tmp_path, record),
            specVersion=spec_version,
            sideEffectClass="none",
        ),
    )


def test_patch_spec_bump_does_not_invalidate_snapshot(tmp_path) -> None:
    # Wart #1: a PATCH spec bump must NOT churn readiness snapshots (only minor/major may).
    from proofsignal_spec import __version__ as SPEC_VERSION

    create_live_write_readiness_workspace(tmp_path)
    major, minor = SPEC_VERSION.split(".")[:2]
    _save_snapshot_with_spec_version(tmp_path, "about-page-unauth", f"{major}.{minor}.99")

    current = readiness_current_state(tmp_path, load_use_case(tmp_path, "about-page-unauth"))

    assert current["status"] == "ready", current
    assert not any(item["code"] == "spec-version-changed" for item in current["invalidationReasons"])


def test_minor_spec_bump_invalidates_snapshot(tmp_path) -> None:
    create_live_write_readiness_workspace(tmp_path)
    _save_snapshot_with_spec_version(tmp_path, "about-page-unauth", "0.0.0")

    current = readiness_current_state(tmp_path, load_use_case(tmp_path, "about-page-unauth"))

    assert any(item["code"] == "spec-version-changed" for item in current["invalidationReasons"])


def test_recording_a_run_does_not_invalidate_the_snapshot(tmp_path) -> None:
    # Regression (dogfood Bug 3): a passing run mutates lastRun/status on the use-case record but
    # must NOT mark the use case stale via "artifact-changed" — only authoring edits should.
    from proofsignal_spec.workspace.repository import save_use_case

    create_live_write_readiness_workspace(tmp_path)
    save_ready_snapshot(tmp_path, "about-page-unauth", side_effect_class="none")

    record = load_use_case(tmp_path, "about-page-unauth")
    record.lastRun = {"runId": "about-page-unauth-20260622T185840Z", "status": "passed"}
    record.status = "ready"
    save_use_case(tmp_path, record)

    current = readiness_current_state(tmp_path, load_use_case(tmp_path, "about-page-unauth"))

    assert current["status"] == "ready", current
    assert not any(item["code"] == "artifact-changed" for item in current["invalidationReasons"])
