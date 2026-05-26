from __future__ import annotations

from proofsignal_spec.cli import create_parser
from proofsignal_spec.workspace.models import RunProfile


def test_cli_accepts_use_case_specific_profile_names() -> None:
    parser = create_parser()
    args = parser.parse_args(["run", "profile-view-unauth", "--profile", "visual-15s"])

    assert args.profile == "visual-15s"


def test_run_profile_serializes_visual_timing() -> None:
    profile = RunProfile.from_dict({"name": "visual-15s", "headed": True, "slowMoMs": 15000})

    assert profile.to_dict() == {"name": "visual-15s", "description": "", "headed": True, "slowMoMs": 15000, "assumePreconditionsReady": False}
