from __future__ import annotations

import time

from verifysignal_spec.commands import list as list_command
from verifysignal_spec.core.adapter import CoreAdapter
from verifysignal_spec.workspace.models import ArtifactReference, RuntimeInputRequirement, UseCaseRecord
from verifysignal_spec.workspace.repository import init_workspace, save_use_case


def test_list_metadata_compatibility_checks_do_not_call_core_and_stay_fast(tmp_path, monkeypatch) -> None:
    init_workspace(tmp_path)
    _create_many_metadata_only_use_cases(tmp_path, count=40)

    def fail_core(*args, **kwargs):  # pragma: no cover - only reached on regression
        raise AssertionError("metadata-only list must not call Core")

    monkeypatch.setattr(CoreAdapter, "contracts", fail_core)
    monkeypatch.setattr(CoreAdapter, "version", fail_core)
    monkeypatch.setattr(CoreAdapter, "run", fail_core)

    start = time.perf_counter()
    result = list_command.run(tmp_path)
    elapsed = time.perf_counter() - start

    assert len(result["useCases"]) == 40
    assert elapsed < 0.050


def _create_many_metadata_only_use_cases(project, *, count: int) -> None:
    (project / ".verifysignal/run-requests").mkdir(parents=True, exist_ok=True)
    (project / ".verifysignal/skills").mkdir(parents=True, exist_ok=True)
    for index in range(count):
        alias = f"read-only-{index:02d}"
        (project / f".verifysignal/run-requests/{alias}.yaml").write_text("{}", encoding="utf-8")
        (project / f".verifysignal/skills/{alias}.browser.md").write_text("# skill\n", encoding="utf-8")
        save_use_case(
            project,
            UseCaseRecord(
                alias=alias,
                title=f"Read Only {index}",
                description="Metadata-only row.",
                runRequest=ArtifactReference(path=f".verifysignal/run-requests/{alias}.yaml", kind="run-request"),
                mainSkill=ArtifactReference(path=f".verifysignal/skills/{alias}.browser.md", kind="skill"),
                skills=[ArtifactReference(path=f".verifysignal/skills/{alias}.browser.md", kind="skill")],
                runtimeInputs=[RuntimeInputRequirement(name="baseUrl", source="default", value="https://example.test")],
                sideEffects={"class": "none"},
                status="ready",
            ),
        )
