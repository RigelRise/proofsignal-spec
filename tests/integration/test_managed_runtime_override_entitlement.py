from __future__ import annotations

import contextlib
import io
import json
from unittest.mock import patch

from helpers import FAKE_CORE
from proofsignal_spec.runtime.entitlement import load_receipt, receipt_path
from proofsignal_spec.runtime.resolver import ensure_core_runtime
from tests.fixtures.managed_runtime import serve_fake_entitlement_backend, write_fake_core_executable
from tests.fixtures.workflows.main_skill_run_coverage import create_main_skill_coverage_workspace


def test_override_core_is_ready_but_not_managed_entitlement_success(tmp_path) -> None:
    result = ensure_core_runtime(tmp_path, explicit_core_cmd=str(FAKE_CORE))
    payload = result.to_dict()

    assert payload["status"] == "ready"
    assert payload["source"] == "explicit"
    assert payload["entitlement"]["status"] == "not-required"
    assert payload["source"] != "managed-download"


def test_override_core_init_exchanges_token_for_protected_operations(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PROOFSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("FAKE_PROOFSIGNAL_MODE", "requires-entitlement")
    monkeypatch.delenv("PROOFSIGNAL_EMAIL_UNLOCK_TOKEN", raising=False)
    monkeypatch.delenv("PROOFSIGNAL_ENTITLEMENT_RECEIPT", raising=False)
    monkeypatch.delenv("PROOFSIGNAL_ENTITLEMENT_RECEIPT_PATH", raising=False)

    with serve_fake_entitlement_backend() as (api_base_url, state):
        result = ensure_core_runtime(
            tmp_path,
            explicit_core_cmd=str(FAKE_CORE),
            api_base_url=api_base_url,
            token="ps_valid",
            integration="claude",
            context="init",
        )

    payload = result.to_dict()
    assert payload["status"] == "ready"
    assert payload["source"] == "explicit"
    assert payload["entitlement"]["status"] == "valid"
    assert load_receipt() is not None
    assert any(request["path"] == "/entitlements/exchange" for request in state.requests)


def test_init_cli_with_override_core_exchanges_interactive_token(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PROOFSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("FAKE_PROOFSIGNAL_MODE", "requires-entitlement")
    monkeypatch.delenv("PROOFSIGNAL_EMAIL", raising=False)
    monkeypatch.delenv("PROOFSIGNAL_EMAIL_UNLOCK_TOKEN", raising=False)
    monkeypatch.delenv("PROOFSIGNAL_ENTITLEMENT_RECEIPT", raising=False)
    monkeypatch.delenv("PROOFSIGNAL_ENTITLEMENT_RECEIPT_PATH", raising=False)

    with serve_fake_entitlement_backend() as (api_base_url, state):
        code, out, err = _cli(
            [
                "init",
                str(tmp_path),
                "--integration",
                "claude",
                "--core-cmd",
                str(FAKE_CORE),
                "--api-base-url",
                api_base_url,
                "--json",
            ],
            stdin="qa@example.com\nps_valid\n",
        )

    assert code == 0, err
    payload = json.loads(out)
    assert payload["runtime"]["source"] == "explicit"
    assert payload["runtime"]["entitlement"]["status"] == "valid"
    assert load_receipt() is not None
    assert [request["path"] for request in state.requests] == [
        "/entitlements/request-token",
        "/entitlements/exchange",
    ]
    assert "qa@example.com" not in out
    assert "ps_valid" not in out


def test_validate_cli_with_override_core_uses_cached_entitlement_receipt(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PROOFSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("FAKE_PROOFSIGNAL_MODE", "requires-entitlement")
    monkeypatch.delenv("PROOFSIGNAL_EMAIL_UNLOCK_TOKEN", raising=False)
    monkeypatch.delenv("PROOFSIGNAL_ENTITLEMENT_RECEIPT", raising=False)
    monkeypatch.delenv("PROOFSIGNAL_ENTITLEMENT_RECEIPT_PATH", raising=False)
    create_main_skill_coverage_workspace(tmp_path)

    with serve_fake_entitlement_backend() as (api_base_url, _state):
        unlocked = ensure_core_runtime(
            tmp_path,
            explicit_core_cmd=str(FAKE_CORE),
            api_base_url=api_base_url,
            token="ps_valid",
            integration="claude",
            context="init",
        )
    assert unlocked.entitlement.status == "valid"

    code, out, err = _cli(
        [
            "validate",
            "profile-view-unauth",
            "--project",
            str(tmp_path),
            "--runtime-readiness",
            "--core-cmd",
            str(FAKE_CORE),
            "--json",
        ]
    )

    assert code == 0, err
    payload = json.loads(out)
    assert payload["status"] == "passed"
    assert payload["managedRuntimeReadiness"]["source"] == "explicit"
    assert payload["managedRuntimeReadiness"]["entitlement"]["status"] == "valid"
    assert payload["authoredEvidenceCoverageStatus"] == "complete"
    assert payload["core"]["status"] == "passed"


def test_validate_cli_with_ancestor_sibling_core_reports_cached_entitlement(tmp_path, monkeypatch) -> None:
    project = tmp_path / "Feats" / "fe-feats"
    project.mkdir(parents=True)
    write_fake_core_executable(project.parent / "proofsignal", mode="requires-entitlement")
    monkeypatch.setenv("PROOFSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("FAKE_PROOFSIGNAL_MODE", "requires-entitlement")
    monkeypatch.delenv("PROOFSIGNAL_CORE_CMD", raising=False)
    monkeypatch.delenv("PROOFSIGNAL_EMAIL_UNLOCK_TOKEN", raising=False)
    monkeypatch.delenv("PROOFSIGNAL_ENTITLEMENT_RECEIPT", raising=False)
    monkeypatch.delenv("PROOFSIGNAL_ENTITLEMENT_RECEIPT_PATH", raising=False)
    create_main_skill_coverage_workspace(project)

    with serve_fake_entitlement_backend() as (api_base_url, _state):
        unlocked = ensure_core_runtime(
            project,
            api_base_url=api_base_url,
            token="ps_valid",
            integration="claude",
            context="init",
        )
    assert unlocked.source == "ancestor-sibling"
    assert unlocked.entitlement.status == "valid"

    code, out, err = _cli(
        [
            "validate",
            "profile-view-unauth",
            "--project",
            str(project),
            "--runtime-readiness",
            "--json",
        ]
    )

    assert code == 0, err
    payload = json.loads(out)
    assert payload["status"] == "passed"
    assert payload["managedRuntimeReadiness"]["source"] == "ancestor-sibling"
    assert payload["managedRuntimeReadiness"]["entitlement"]["status"] == "valid"
    assert payload["core"]["status"] == "passed"


def test_validate_cli_with_override_core_blocks_expired_receipt_before_core_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PROOFSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("FAKE_PROOFSIGNAL_MODE", "requires-entitlement")
    monkeypatch.delenv("PROOFSIGNAL_EMAIL_UNLOCK_TOKEN", raising=False)
    monkeypatch.delenv("PROOFSIGNAL_ENTITLEMENT_RECEIPT", raising=False)
    monkeypatch.delenv("PROOFSIGNAL_ENTITLEMENT_RECEIPT_PATH", raising=False)
    create_main_skill_coverage_workspace(tmp_path)
    path = receipt_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "receiptSummary": {
                    "receiptId": "rcpt_expired",
                    "status": "valid",
                    "expiresAt": "2000-01-01T00:00:00Z",
                }
            }
        ),
        encoding="utf-8",
    )

    code, out, err = _cli(
        [
            "validate",
            "profile-view-unauth",
            "--project",
            str(tmp_path),
            "--runtime-readiness",
            "--core-cmd",
            str(FAKE_CORE),
            "--json",
        ]
    )

    assert code == 2, err
    payload = json.loads(out)
    assert payload["status"] == "blocked"
    assert payload["managedRuntimeReadiness"]["source"] == "none"
    assert payload["managedRuntimeReadiness"]["entitlement"]["status"] == "expired"
    assert payload["blockers"][0]["code"] == "entitlement.expired"


def _cli(args: list[str], *, stdin: str = "") -> tuple[int, str, str]:
    from proofsignal_spec.cli import main

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr), patch("sys.stdin", _TtyInput(stdin)):
        code = main(args)
    return code, stdout.getvalue(), stderr.getvalue()


class _TtyInput(io.StringIO):
    def isatty(self) -> bool:
        return True
