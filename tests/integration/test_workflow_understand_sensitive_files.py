from __future__ import annotations

from verifysignal_spec.workspace.repository import init_workspace
from verifysignal_spec.workflows.repository_context import collect_safe_repository_context


def test_understand_avoids_sensitive_files(tmp_path) -> None:
    init_workspace(tmp_path)
    (tmp_path / ".env").write_text("PASSWORD=secret\n", encoding="utf-8")
    context = collect_safe_repository_context(tmp_path, [".env", "README.md"])
    assert ".env" in context["blockedSensitivePaths"]

