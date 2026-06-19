from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _template(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_agent_command_guidance_uses_canonical_side_effect_policy_and_supersede_flow() -> None:
    combined = "\n".join(
        _template(f"src/proofsignal_spec/templates/agent-commands/proofsignal.{stage}.md")
        for stage in ["specify", "clarify", "plan", "implement", "validate", "run", "repair"]
    )

    assert "sideEffectPolicy.allowed[]" in combined
    assert "sideEffectPolicy.forbidden[]" in combined
    assert "sideEffectPolicy.rules[].effect/match" in combined
    assert "Do not author" in combined
    assert "workflow supersede-write-outcome" in combined
    assert "runtime-supported confirmation" in combined
    assert "prepared/committed/discarded" in combined


def test_workflow_template_documents_canonical_policy_without_legacy_examples() -> None:
    content = _template("src/proofsignal_spec/templates/workflows/proofsignal-use-case.yaml")

    assert "sideEffectPolicy.allowed[]" in content
    assert "sideEffectPolicy.forbidden[]" in content
    assert "sideEffectPolicy.rules[].effect/match" in content
    assert "Do not author" in content
