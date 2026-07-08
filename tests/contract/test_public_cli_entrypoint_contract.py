from __future__ import annotations

from pathlib import Path

from verifysignal_spec.cli import create_parser


def test_public_and_alias_console_scripts_are_declared() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert 'verifysignal = "verifysignal_spec.cli:main"' in pyproject
    assert 'verifysignal-spec = "verifysignal_spec.cli:main"' in pyproject


def test_public_entrypoint_can_render_public_help_name() -> None:
    parser = create_parser(prog="verifysignal")

    assert parser.prog == "verifysignal"
    assert "VerifySignal CLI" in parser.description

