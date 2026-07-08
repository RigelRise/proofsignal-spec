from __future__ import annotations

from time import perf_counter

from verifysignal_spec.commands.runtime_inputs import resolve_runtime_inputs
from verifysignal_spec.workspace.models import RuntimeInputRequirement
from verifysignal_spec.workflows.write_safety import resolve_confirmation_signal_placeholders


def test_generated_and_confirmation_preparation_stays_local_and_fast() -> None:
    requirements = [
        RuntimeInputRequirement(
            name=f"resourceName{index}",
            source="generated",
            value=f"VerifySignal QA {index}",
            refreshOnRerunAfterCommit=True,
        )
        for index in range(20)
    ]
    signals = [
        {
            "id": f"confirm-{index}",
            "type": "runtimeOutput",
            "reference": f"output{index}",
            "expectedContains": f"{{{{parameters.resourceName{index}}}}}",
        }
        for index in range(20)
    ]

    started = perf_counter()
    for attempt in range(50):
        values = resolve_runtime_inputs(
            requirements,
            interactive=False,
            run_id=f"add-collaboration-project-20260619T17{attempt:04d}Z",
            refresh_names={item.name for item in requirements},
        )
        _resolved, findings = resolve_confirmation_signal_placeholders(signals, values)
        assert findings == []

    elapsed = perf_counter() - started
    assert elapsed / 50 < 0.05
