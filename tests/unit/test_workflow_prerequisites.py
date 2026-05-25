from __future__ import annotations

import pytest

from proofsignal_spec.workflows.prerequisites import check_prerequisites

from tests.fixtures.workflows.prerequisites import create_missing_understanding_workspace


def test_missing_understanding_blocks_specify(tmp_path) -> None:
    create_missing_understanding_workspace(tmp_path)
    result = check_prerequisites(tmp_path, "specify")
    assert result["status"] == "missing"
    assert result["canProceed"] is False
    assert result["requiresConfirmation"] is False
    assert ".proofsignal/workflows/understanding.md" in result["missingArtifacts"]
    assert ".proofsignal/product-context.yaml" in result["missingArtifacts"]
    assert result["nextCommand"] == "/proofsignal-understand"


def test_understand_and_list_do_not_require_repository_understanding(tmp_path) -> None:
    create_missing_understanding_workspace(tmp_path)
    assert check_prerequisites(tmp_path, "understand")["status"] == "ready"
    assert check_prerequisites(tmp_path, "list")["status"] == "ready"


def test_invalid_alias_uses_path_safe_alias_rules(tmp_path) -> None:
    create_missing_understanding_workspace(tmp_path)
    with pytest.raises(ValueError, match="Alias must be lowercase path-safe"):
        check_prerequisites(tmp_path, "clarify", alias="../bad")
