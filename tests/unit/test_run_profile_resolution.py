from __future__ import annotations

from verifysignal_spec.cli import create_parser
from verifysignal_spec.commands.run import resolve_effective_profile_settings
from verifysignal_spec.workspace.models import RunProfile


def test_cli_accepts_use_case_specific_profile_names() -> None:
    parser = create_parser()
    args = parser.parse_args(["run", "profile-view-unauth", "--profile", "visual-15s"])

    assert args.profile == "visual-15s"


def test_cli_accepts_slow_motion_override() -> None:
    parser = create_parser()
    args = parser.parse_args(["run", "profile-view-unauth", "--profile", "debug", "--slow-mo", "1200"])

    assert args.slow_mo == 1200


def test_run_profile_serializes_visual_timing() -> None:
    profile = RunProfile.from_dict({"name": "visual-15s", "headed": True, "slowMoMs": 15000})

    assert profile.to_dict() == {"name": "visual-15s", "description": "", "headed": True, "slowMoMs": 15000, "assumePreconditionsReady": False}


def test_debug_profile_uses_900ms_default_when_profile_has_no_explicit_slowmo() -> None:
    settings = resolve_effective_profile_settings(RunProfile.from_dict({"name": "debug", "headed": True}))

    assert settings.to_dict() == {"profile": "debug", "headed": True, "slowMoMs": 900, "source": "default", "overrides": []}


def test_profile_slowmo_override_precedence() -> None:
    settings = resolve_effective_profile_settings(RunProfile.from_dict({"name": "debug", "headed": True, "slowMoMs": 700}), slow_mo_override=1200)

    assert settings.to_dict() == {"profile": "debug", "headed": True, "slowMoMs": 1200, "source": "cli-override", "overrides": ["slowMoMs"]}


def test_normal_profile_keeps_zero_slowmo_default() -> None:
    settings = resolve_effective_profile_settings(RunProfile.from_dict({"name": "normal", "headed": False}))

    assert settings.to_dict() == {"profile": "normal", "headed": False, "slowMoMs": 0, "source": "default", "overrides": []}
