from __future__ import annotations

import pytest

from proofsignal_spec.workspace.repository import init_workspace
from proofsignal_spec.workflows.repository import save_workflow_state


def test_workflow_state_rejects_secret_values(tmp_path) -> None:
    init_workspace(tmp_path)
    with pytest.raises(ValueError):
        save_workflow_state(tmp_path, "login", {"schemaVersion": "proofsignal-spec-workflow-state/v1", "password": "real-secret-value"})

