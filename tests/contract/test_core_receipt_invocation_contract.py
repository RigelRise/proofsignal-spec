from __future__ import annotations

import os
from pathlib import Path

from helpers import FAKE_CORE
from proofsignal_spec.core.adapter import CoreAdapter
from proofsignal_spec.core.contracts import core_entitlement_blocker_code


def test_version_call_does_not_receive_entitlement_receipt(tmp_path: Path, monkeypatch) -> None:
    receipt = tmp_path / "receipt.json"
    receipt.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("FAKE_PROOFSIGNAL_MODE", "requires-entitlement")

    payload = CoreAdapter(executable=str(FAKE_CORE), cwd=tmp_path).version()

    assert payload["operation"] == "version"


def test_protected_operation_receives_receipt_reference_via_environment(tmp_path: Path, monkeypatch) -> None:
    receipt = tmp_path / "receipt.json"
    receipt.write_text("{}", encoding="utf-8")
    run_request = tmp_path / "run.yaml"
    skill = tmp_path / "skill.md"
    run_request.write_text("{}", encoding="utf-8")
    skill.write_text("# skill", encoding="utf-8")
    monkeypatch.setenv("FAKE_PROOFSIGNAL_MODE", "requires-entitlement")
    monkeypatch.delenv("PROOFSIGNAL_ENTITLEMENT_RECEIPT", raising=False)

    payload = CoreAdapter(executable=str(FAKE_CORE), cwd=tmp_path).authoring_check(
        run_request,
        skill,
        [skill],
        entitlement_receipt=receipt,
    )

    assert payload["operation"] == "authoring-check"
    assert os.environ.get("PROOFSIGNAL_ENTITLEMENT_RECEIPT") is None


def test_core_entitlement_errors_map_to_public_runtime_blockers(tmp_path: Path, monkeypatch) -> None:
    receipt = tmp_path / "receipt.json"
    receipt.write_text("{}", encoding="utf-8")
    run_request = tmp_path / "run.yaml"
    skill = tmp_path / "skill.md"
    run_request.write_text("{}", encoding="utf-8")
    skill.write_text("# skill", encoding="utf-8")
    monkeypatch.setenv("FAKE_PROOFSIGNAL_MODE", "rejects-entitlement")

    payload = CoreAdapter(executable=str(FAKE_CORE), cwd=tmp_path).authoring_check(
        run_request,
        skill,
        [skill],
        entitlement_receipt=receipt,
    )

    assert payload["status"] == "blocked"
    assert core_entitlement_blocker_code(payload) == "entitlement.rejected"
