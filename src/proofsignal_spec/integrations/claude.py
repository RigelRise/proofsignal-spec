from __future__ import annotations

from pathlib import Path

from proofsignal_spec.templates.agent_guidance import (
    FIRST_RUN_STAGE_CARD_GUIDANCE,
    MISSING_UNDERSTANDING_AUTO_PREPARE,
    PLAYWRIGHT_MCP_GUIDANCE,
    REAL_TARGET_FIRST_RECOMMENDATION,
)

from .base import AgentIntegration, RenderedFile, build_onboarding_guidance, render_onboarding_guide, render_workflow_skill_files


class ClaudeIntegration(AgentIntegration):
    key = "claude"
    display_name = "Claude Code"
    invoke_style = "Claude Code slash skills under .claude/skills/proofsignal-*; invoke as /proofsignal-*"

    def render_files(self, project: Path, core_status: dict[str, object] | None = None) -> list[RenderedFile]:
        files = [
            RenderedFile("CLAUDE.md", _context(), "claude/context", "context"),
        ]
        guide = build_onboarding_guidance(
            integration_key=self.key,
            display_name=self.display_name,
            generated_guide_path=".claude/PROOFSIGNAL_ONBOARDING.md",
            core_status=core_status,
        )
        files.append(RenderedFile(".claude/PROOFSIGNAL_ONBOARDING.md", render_onboarding_guide(guide), "claude/onboarding-guide", "onboarding-guide"))
        files.extend(render_workflow_skill_files(".claude/skills", "Claude Code", include_argument_hint=True))
        return files


def _context() -> str:
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

To change ONLY a use case's side-effect policy (class/mode/allowed/forbidden),
use `proofsignal policy set <alias> --class <class> [--mode <mode>] [--payload
<policy.json>]`. It mutates only the policy, re-syncs the run request, and
preserves runtime inputs and skills — do NOT re-author the full `implement`
payload to declare or change a policy. Re-persist `implement` only for
skill/target/step/resourceIdentity/rerun-policy changes.

Golden Path first runs are agent-chat first. {REAL_TARGET_FIRST_RECOMMENDATION}.
{FIRST_RUN_STAGE_CARD_GUIDANCE}.
{MISSING_UNDERSTANDING_AUTO_PREPARE}.

{PLAYWRIGHT_MCP_GUIDANCE}.
"""
