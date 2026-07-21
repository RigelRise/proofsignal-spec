from __future__ import annotations

from pathlib import Path

from verifysignal_spec.runtime.telemetry import ping_outcome, send_usage_ping, usage_ping_enabled
from tests.fixtures.managed_runtime import serve_fake_entitlement_backend


def _usage_requests(state) -> list[dict]:
    return [r for r in state.requests if r.get("path") == "/entitlements/usage"]


def test_usage_ping_default_on_dispatches_to_backend(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.delenv("VERIFYSIGNAL_USAGE_PING", raising=False)

    with serve_fake_entitlement_backend() as (api_base_url, state):
        thread = send_usage_ping("run", "pass", api_base_url=api_base_url, block=True)

    assert thread is not None
    assert state.usage_count == 1
    assert len(_usage_requests(state)) == 1


def test_usage_ping_opt_out_sends_nothing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("VERIFYSIGNAL_USAGE_PING", "0")

    assert usage_ping_enabled() is False
    with serve_fake_entitlement_backend() as (api_base_url, state):
        thread = send_usage_ping("run", "pass", api_base_url=api_base_url, block=True)

    assert thread is None
    assert state.usage_count == 0
    assert _usage_requests(state) == []


def test_usage_ping_never_raises_when_offline(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.delenv("VERIFYSIGNAL_USAGE_PING", raising=False)

    # Dead port: the ping must swallow the transport error and never surface it to the command.
    send_usage_ping("run", "pass", api_base_url="http://127.0.0.1:1/api", block=True)  # must not raise


def test_usage_ping_payload_is_minimal_and_pii_free(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.delenv("VERIFYSIGNAL_USAGE_PING", raising=False)

    with serve_fake_entitlement_backend() as (api_base_url, state):
        send_usage_ping("check", "blocked", api_base_url=api_base_url, block=True)

    payload = _usage_requests(state)[0]["payload"]
    assert payload["command"] == "check"
    assert payload["outcome"] == "blocked"
    # Only command + outcome + client — no project data, no PII.
    assert set(payload) <= {"schema", "schemaVersion", "command", "outcome", "client"}
    assert "@" not in __import__("json").dumps(payload)


def test_first_run_notice_prints_once_to_stderr(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.delenv("VERIFYSIGNAL_USAGE_PING", raising=False)
    # The notice is TTY-only (a human at a terminal); simulate one.
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)

    with serve_fake_entitlement_backend() as (api_base_url, _state):
        send_usage_ping("run", "pass", api_base_url=api_base_url, block=True)
        first = capsys.readouterr()
        send_usage_ping("run", "pass", api_base_url=api_base_url, block=True)
        second = capsys.readouterr()

    # Disclosed once, on stderr (stdout must stay clean for JSON), with the opt-out named.
    assert "usage ping" in first.err
    assert "VERIFYSIGNAL_USAGE_PING=0" in first.err
    assert first.out == ""
    assert second.err == ""


def test_opted_out_user_sees_no_notice(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("VERIFYSIGNAL_USAGE_PING", "0")
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)

    send_usage_ping("run", "pass", api_base_url="http://127.0.0.1:1/api", block=True)

    assert capsys.readouterr().err == ""


def test_no_notice_when_not_a_tty(tmp_path: Path, monkeypatch, capsys) -> None:
    # Piped/CI invocations must keep stderr clean (the public CLI contract asserts empty stderr on
    # --json runs); disclosure there is the documented ToS/Privacy.
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.delenv("VERIFYSIGNAL_USAGE_PING", raising=False)

    with serve_fake_entitlement_backend() as (api_base_url, _state):
        send_usage_ping("run", "pass", api_base_url=api_base_url, block=True)

    assert capsys.readouterr().err == ""


def test_ping_outcome_maps_statuses() -> None:
    assert ping_outcome("passed") == "pass"
    assert ping_outcome("failed") == "fail"
    assert ping_outcome("blocked") == "blocked"
    assert ping_outcome("weird") == "error"
    assert ping_outcome(None) == "error"
