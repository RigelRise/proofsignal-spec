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


# --- Honest-readiness model (cadeado, não amarelo): ceiling states + kill no-op commands -------


def test_credentialed_read_is_ready_with_lock_not_yellow(tmp_path) -> None:
    # A credentialed read that PASSED is a trusted ceiling (credentials re-checked at run), NOT a
    # yellow 'needs-validate' loop. It must read as a green-with-lock state with no suggested command.
    create_live_write_readiness_workspace(tmp_path)
    save_ready_snapshot(tmp_path, "brands-search-authenticated")

    current = readiness_current_state(tmp_path, load_use_case(tmp_path, "brands-search-authenticated"))

    assert current["status"] == "ready-credential-bound", current
    assert current["presentation"]["ceiling"] is True
    assert current["presentation"]["icon"] == "🔒"
    assert current["nextAction"] is None
    assert any(item["code"] == "environment-bound" for item in current["invalidationReasons"])


def test_committed_write_lock_has_no_no_op_command(tmp_path) -> None:
    # A committed write that PASSED is a trusted ceiling: lock 🔒 'confirm before next run', and the
    # old no-op 'workflow check run' suggestion is gone (running it changed nothing).
    from proofsignal_spec.workspace.repository import save_use_case
    from tests.fixtures.workflows.side_effect_contract_alignment import confirmable_write_last_run

    create_live_write_readiness_workspace(tmp_path)
    save_ready_snapshot(tmp_path, "add-collaboration-project", side_effect_class="write")

    record = load_use_case(tmp_path, "add-collaboration-project")
    record.lastRun = confirmable_write_last_run(run_id="add-collaboration-project-fresh")
    save_use_case(tmp_path, record)

    current = readiness_current_state(tmp_path, load_use_case(tmp_path, "add-collaboration-project"))

    assert current["status"] == "needs-rerun-confirmation", current
    assert current["presentation"]["icon"] == "🔒"
    assert current["presentation"]["ceiling"] is True
    assert current["nextAction"] is None


def test_committed_write_with_matching_supersede_review_is_confirmed(tmp_path) -> None:
    # Bug #2: once the owner supersedes/approves the committed write (review sourceRunId == lastRun
    # runId), the badge must FLIP to 🔓 'rerun confirmed' — the gate already honors the review; the
    # badge now reads the same source so the owner's action is visible.
    from proofsignal_spec.workspace.models import SupersedeReview
    from proofsignal_spec.workspace.repository import save_supersede_review, save_use_case
    from tests.fixtures.workflows.side_effect_contract_alignment import (
        confirmable_write_last_run,
        supersede_review_payload,
    )

    create_live_write_readiness_workspace(tmp_path)
    save_ready_snapshot(tmp_path, "add-collaboration-project", side_effect_class="write")

    run_id = "add-collaboration-project-20260622T202124Z"
    record = load_use_case(tmp_path, "add-collaboration-project")
    record.lastRun = confirmable_write_last_run(run_id=run_id)
    save_use_case(tmp_path, record)
    save_supersede_review(
        tmp_path,
        "add-collaboration-project",
        SupersedeReview.from_dict(supersede_review_payload(source_run_id=run_id)),
    )

    current = readiness_current_state(tmp_path, load_use_case(tmp_path, "add-collaboration-project"))

    assert current["status"] == "rerun-confirmed", current
    assert current["presentation"]["icon"] == "🔓"
    assert current["presentation"]["ceiling"] is True
    assert current["nextAction"] is None


def test_supersede_review_for_a_different_run_does_not_confirm(tmp_path) -> None:
    # Guard: a review tied to a DIFFERENT runId must not confirm the current run.
    from proofsignal_spec.workspace.models import SupersedeReview
    from proofsignal_spec.workspace.repository import save_supersede_review, save_use_case
    from tests.fixtures.workflows.side_effect_contract_alignment import (
        confirmable_write_last_run,
        supersede_review_payload,
    )

    create_live_write_readiness_workspace(tmp_path)
    save_ready_snapshot(tmp_path, "add-collaboration-project", side_effect_class="write")

    record = load_use_case(tmp_path, "add-collaboration-project")
    record.lastRun = confirmable_write_last_run(run_id="current-run")
    save_use_case(tmp_path, record)
    save_supersede_review(
        tmp_path,
        "add-collaboration-project",
        SupersedeReview.from_dict(supersede_review_payload(source_run_id="some-older-run")),
    )

    current = readiness_current_state(tmp_path, load_use_case(tmp_path, "add-collaboration-project"))

    assert current["status"] == "needs-rerun-confirmation", current


def test_blocked_snapshot_beats_stale_and_offers_a_command(tmp_path) -> None:
    # A blocked (failed-validation) snapshot must not be silently relabeled 'stale' just because it
    # is also old, and it must offer a recovery command (today: None, violating the list template).
    from datetime import UTC, datetime, timedelta

    from proofsignal_spec import __version__ as SPEC_VERSION
    from proofsignal_spec.workspace.models import ReadinessSnapshot
    from proofsignal_spec.workspace.repository import artifact_fingerprints, save_readiness_snapshot

    create_live_write_readiness_workspace(tmp_path)
    record = load_use_case(tmp_path, "about-page-unauth")
    old = (datetime.now(UTC) - timedelta(days=400)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    save_readiness_snapshot(
        tmp_path,
        ReadinessSnapshot(
            alias="about-page-unauth",
            status="blocked",
            checkedAt=old,
            artifactFingerprints=artifact_fingerprints(tmp_path, record),
            specVersion=SPEC_VERSION,
            sideEffectClass="none",
        ),
    )

    current = readiness_current_state(tmp_path, load_use_case(tmp_path, "about-page-unauth"))

    assert current["status"] == "blocked", current
    assert "validate" in (current["nextAction"] or "")


def test_not_checked_offers_a_validate_command(tmp_path) -> None:
    # First contact must not be a dead-end: surface the escape command.
    create_live_write_readiness_workspace(tmp_path)

    current = readiness_current_state(tmp_path, load_use_case(tmp_path, "about-page-unauth"))

    assert current["status"] == "not-checked"
    assert "validate" in (current.get("nextAction") or "")
    assert current["presentation"]["ceiling"] is False


def test_stale_committed_write_discloses_pending_rerun_gate(tmp_path) -> None:
    # When freshness drift and the write-rerun guard co-exist, freshness wins (status stays stale),
    # but the still-pending rerun gate must be disclosed so it does not ambush the owner after re-check.
    from proofsignal_spec.workspace.repository import save_use_case
    from tests.fixtures.workflows.side_effect_contract_alignment import confirmable_write_last_run

    create_live_write_readiness_workspace(tmp_path)
    save_ready_snapshot(tmp_path, "add-collaboration-project", checked_at=old_checked_at(hours=25), side_effect_class="write")

    record = load_use_case(tmp_path, "add-collaboration-project")
    record.lastRun = confirmable_write_last_run()
    save_use_case(tmp_path, record)

    current = readiness_current_state(tmp_path, load_use_case(tmp_path, "add-collaboration-project"))

    assert current["status"] == "stale", current
    assert current.get("pendingCeilingNote")


def test_stale_and_needs_validate_labels_are_distinct() -> None:
    # The two share 'Needs validation' today, hiding which of two different remediations applies.
    from proofsignal_spec.workspace.repository import _current_label

    assert _current_label("stale") != _current_label("needs-validate")


def test_next_action_present_iff_state_is_actionable() -> None:
    # The honesty invariant: a status carries a suggested command IF AND ONLY IF running it can move
    # the state. Ceiling (lock) and plain ready carry none; needs-validate/stale/blocked/not-checked do.
    from proofsignal_spec.workspace.repository import _readiness_next_action, _readiness_presentation

    for status in [
        "ready",
        "ready-credential-bound",
        "needs-rerun-confirmation",
        "rerun-confirmed",
        "needs-validate",
        "stale",
        "blocked",
        "not-checked",
    ]:
        has_action = _readiness_next_action(status, "alias") is not None
        ceiling = _readiness_presentation(status)["ceiling"]
        if status == "ready" or ceiling:
            assert not has_action, status
        else:
            assert has_action, status


def test_patch_bump_keeps_readiness_minor_stable() -> None:
    # Guard: the MCP-guidance increment is a PATCH (0.17.0 -> 0.17.1) precisely so it does NOT churn
    # readiness snapshots. A future careless minor bump that would re-invalidate must trip this.
    from proofsignal_spec.workspace.repository import _spec_minor

    assert _spec_minor("0.17.1") == _spec_minor("0.17.0")
    assert _spec_minor("0.18.0") != _spec_minor("0.17.0")
