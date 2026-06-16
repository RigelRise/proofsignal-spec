from __future__ import annotations

import time

from proofsignal_spec.commands.list import run as list_run
from tests.fixtures.workflows.live_write_readiness import create_live_write_readiness_workspace


def test_representative_list_readiness_metadata_overhead_under_fifty_ms(tmp_path) -> None:
    create_live_write_readiness_workspace(tmp_path)

    started = time.monotonic()
    payload = list_run(tmp_path)
    elapsed = time.monotonic() - started

    assert len(payload["useCases"]) == 3
    assert elapsed < 0.05
