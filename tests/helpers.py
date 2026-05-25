from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

FAKE_CORE = ROOT / "tests" / "fixtures" / "proofsignal-core" / "fake_proofsignal.py"


class CliTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        self.old_core = os.environ.get("PROOFSIGNAL_CORE_CMD")
        self.old_mode = os.environ.get("FAKE_PROOFSIGNAL_MODE")
        os.environ["PROOFSIGNAL_CORE_CMD"] = str(FAKE_CORE)
        os.environ.pop("FAKE_PROOFSIGNAL_MODE", None)

    def tearDown(self) -> None:
        self.tmp.cleanup()
        if self.old_core is None:
            os.environ.pop("PROOFSIGNAL_CORE_CMD", None)
        else:
            os.environ["PROOFSIGNAL_CORE_CMD"] = self.old_core
        if self.old_mode is None:
            os.environ.pop("FAKE_PROOFSIGNAL_MODE", None)
        else:
            os.environ["FAKE_PROOFSIGNAL_MODE"] = self.old_mode

    def cli(self, args: list[str]) -> tuple[int, str, str]:
        from proofsignal_spec.cli import main

        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(args)
        return code, stdout.getvalue(), stderr.getvalue()
