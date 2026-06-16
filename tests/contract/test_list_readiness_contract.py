from __future__ import annotations

from proofsignal_spec.commands.list import run as list_run
from tests.fixtures.workflows.live_write_readiness import create_live_write_readiness_workspace, save_ready_snapshot
from tests.helpers import assert_compact_readiness_row, row_by_alias


def test_list_contract_separates_historical_last_run_from_current_readiness(tmp_path) -> None:
    create_live_write_readiness_workspace(tmp_path)

    payload = list_run(tmp_path)
    row = row_by_alias(payload, "add-collaboration-project")

    assert_compact_readiness_row(row)
    assert row["lastRun"]["status"] == "passed"
    assert row["current"]["status"] == "not-checked"
    assert row["risk"]["write"] is True
    assert row["requirements"]["sideEffectClass"] == "write"


def test_list_contract_shows_last_checked_ready_only_from_snapshot(tmp_path) -> None:
    create_live_write_readiness_workspace(tmp_path)
    save_ready_snapshot(tmp_path, "about-page-unauth")

    payload = list_run(tmp_path)
    row = row_by_alias(payload, "about-page-unauth")

    assert row["lastRun"]["status"] == "passed"
    assert row["current"]["status"] == "ready"
    assert row["current"]["checked"] is True
    assert row["requirements"]["credentials"] == []
