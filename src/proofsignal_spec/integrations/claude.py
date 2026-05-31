from __future__ import annotations

from pathlib import Path

from proofsignal_spec.templates.agent_guidance import (
    BROWSER_TARGET_BEFORE_PLANNING,
    CONFIRMED_REPAIR_BOUNDARY,
    FIRST_RUN_STAGE_CARD_GUIDANCE,
    MISSING_UNDERSTANDING_AUTO_PREPARE,
    PUBLIC_WORKFLOW_CONTRACT_BOUNDARY,
    REAL_TARGET_FIRST_RECOMMENDATION,
    RUNTIME_READINESS_BOUNDARY,
    SAFE_MECHANICAL_REPAIR_GUIDANCE,
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
        for name in ["author", "refine", "plan", "check", "list", "validate", "run", "repair"]:
            files.append(
                RenderedFile(
                    f".claude/skills/proofsignal-spec-{name}/SKILL.md",
                    _skill(name),
                    f"claude/proofsignal-spec-{name}",
                )
            )
        return files


def _context() -> str:
    return f"""# ProofSignal Spec Agent Guidance

Use `/proofsignal-*` workflow skills for staged ProofSignal use case authoring.
Use `proofsignal-spec` commands from the target repository root for deterministic
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


def _skill(name: str) -> str:
    title = f"proofsignal-spec-{name}"
    description, argument_hint, body = _workflow_copy(name)
    return f"""---
name: "{title}"
description: "Claude Code workflow for ProofSignal Spec {name}: {description}"
argument-hint: "{argument_hint}"
---

# {title}

Work inside the target repository and use the `.proofsignal/` workspace.

- Keep generated docs, run requests, skills, and guidance in English.
- Store generated run requests under `.proofsignal/run-requests/`.
- Store reusable skills under `.proofsignal/skills/`.
- A use case references exactly one run request; skills may be reused.
- Avoid sensitive files by default and ask before reading local env or secrets.
- Validate through `proofsignal-spec validate <alias>` before marking ready.
- {PUBLIC_WORKFLOW_CONTRACT_BOUNDARY}.
- {FIRST_RUN_STAGE_CARD_GUIDANCE}.
- {MISSING_UNDERSTANDING_AUTO_PREPARE}.
- {SAFE_MECHANICAL_REPAIR_GUIDANCE}.
- Never persist credential values.

## Slash Command

Invoke this workflow as `/{title}`.

## Workflow

{body}
"""


def _workflow_copy(name: str) -> tuple[str, str, str]:
    workflows = {
        "author": (
            "create a browser validation use case",
            '<alias> "<description>"',
            f"Gather the target behavior and browser target. {BROWSER_TARGET_BEFORE_PLANNING}. Then run `proofsignal-spec author <alias> \"<description>\"`. Keep one use case mapped to one run request and write reusable skills under `.proofsignal/skills/`.",
        ),
        "refine": (
            "improve an existing use case",
            "<alias>",
            "Inspect the selected use case record and related run request or skills, ask focused questions for missing product knowledge, then update only the relevant `.proofsignal/` artifacts.",
        ),
        "plan": (
            "plan ProofSignal artifact changes",
            "<alias or validation goal>",
            "Review repository context and the requested validation goal, then produce a concise implementation plan for the run request and reusable skills before editing artifacts.",
        ),
        "check": (
            "check workspace and Core readiness",
            "",
            "Run `proofsignal-spec check` and summarize workspace, integration, and Core readiness issues with the exact next command the user should run.",
        ),
        "list": (
            "list registered ProofSignal use cases",
            "",
            "Run `proofsignal-spec list` and summarize aliases, status, runtime requirements, and the latest result. Do not inspect sensitive files.",
        ),
        "validate": (
            "validate a use case through ProofSignal Core",
            "<alias>",
            f"Run `proofsignal-spec validate <alias> --runtime-readiness` when runtime readiness matters; {RUNTIME_READINESS_BOUNDARY}. Summarize Core findings without exposing secret values.",
        ),
        "run": (
            "run a registered use case",
            "<alias> [normal|debug]",
            "Run `proofsignal-spec run <alias> --profile normal` unless the user requests `debug`. For an accepted Golden Path first run, present `firstRunStatus`, `strictPass`, stage cards, primary evidence, and next action. If required runtime inputs are missing, ask only for the missing values and never persist credentials.",
        ),
        "repair": (
            "repair invalid or failed use cases",
            "<alias> [report path]",
            f"Run `proofsignal-spec repair <alias>` or include `--from-report <path>` when the user provides a report. {SAFE_MECHANICAL_REPAIR_GUIDANCE}. Present auto-applied repair feedback clearly and ask before any confirmation-required change.",
        ),
    }
    return workflows[name]
