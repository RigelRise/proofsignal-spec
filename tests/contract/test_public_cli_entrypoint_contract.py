from __future__ import annotations

from pathlib import Path

from proofsignal_spec.cli import create_parser


def test_public_and_alias_console_scripts_are_declared() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert 'proofsignal = "proofsignal_spec.cli:main"' in pyproject
    assert 'proofsignal-spec = "proofsignal_spec.cli:main"' in pyproject


def test_public_entrypoint_can_render_public_help_name() -> None:
    parser = create_parser(prog="proofsignal")

    assert parser.prog == "proofsignal"
    assert "ProofSignal CLI" in parser.description

