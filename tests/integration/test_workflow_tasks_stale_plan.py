from __future__ import annotations

from verifysignal_spec.workspace.repository import init_workspace
from verifysignal_spec.workflows.engine import create_workflow_run, generate_tasks, plan_artifacts
from verifysignal_spec.workflows.repository import load_artifact_plan, fingerprint_text


def test_plan_fingerprint_changes_when_plan_document_changes(tmp_path) -> None:
    init_workspace(tmp_path)
    create_workflow_run(tmp_path, "Validate login.", alias="login", integration="codex")
    plan_artifacts(tmp_path, "login")
    first = generate_tasks(tmp_path, "login")
    plan_md = tmp_path / ".verifysignal" / "workflows" / "use-cases" / "login" / "plan.md"
    plan_md.write_text(plan_md.read_text(encoding="utf-8") + "\nExtra note.\n", encoding="utf-8")
    assert first["planFingerprint"] != fingerprint_text(plan_md.read_text(encoding="utf-8"))

