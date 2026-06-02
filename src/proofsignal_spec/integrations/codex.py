from __future__ import annotations

from pathlib import Path

from proofsignal_spec.templates.agent_guidance import (
    FIRST_RUN_STAGE_CARD_GUIDANCE,
    MISSING_UNDERSTANDING_AUTO_PREPARE,
    REAL_TARGET_FIRST_RECOMMENDATION,
)

from .base import AgentIntegration, RenderedFile, build_onboarding_guidance, render_onboarding_guide, render_workflow_skill_files


class CodexIntegration(AgentIntegration):
    key = "codex"
    display_name = "Codex"
    invoke_style = "Codex skills under .agents/skills/proofsignal-*; invoke as /proofsignal-*"

    def render_files(self, project: Path, core_status: dict[str, object] | None = None) -> list[RenderedFile]:
        files = [
            RenderedFile("AGENTS.md", _context("AGENTS.md"), "codex/context", "context"),
        ]
        guide = build_onboarding_guidance(
            integration_key=self.key,
            display_name=self.display_name,
            generated_guide_path=".agents/PROOFSIGNAL_ONBOARDING.md",
            core_status=core_status,
        )
        files.append(RenderedFile(".agents/PROOFSIGNAL_ONBOARDING.md", render_onboarding_guide(guide), "codex/onboarding-guide", "onboarding-guide"))
        files.extend(render_workflow_skill_files(".agents/skills", "Codex"))
        return files


def _context(filename: str) -> str:
    return f"""# ProofSignal Spec Agent Guidance

Use `/proofsignal-*` workflow skills for staged ProofSignal use case authoring.
Use `proofsignal` commands from the target repository root for deterministic
non-AI operations. Keep generated project artifacts and guidance in English.
Use pt-BR only for conversation with the project owner when appropriate. Store
ProofSignal Spec state in `.proofsignal/`. Do not import private ProofSignal
Core packages.

Avoid sensitive files by default and ask before reading local environment files
or secret-bearing configuration. Never persist credential values.

Each use case maps to exactly one run request. Skills are decoupled reusable
artifacts that may support multiple run requests. Store staged workflow
documents under `.proofsignal/workflows/` and use structured workflow state for
status, gates, and resume.

Golden Path first runs are agent-chat first. {REAL_TARGET_FIRST_RECOMMENDATION}.
{FIRST_RUN_STAGE_CARD_GUIDANCE}.
{MISSING_UNDERSTANDING_AUTO_PREPARE}.
"""
