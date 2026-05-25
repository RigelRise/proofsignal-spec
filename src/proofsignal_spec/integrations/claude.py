from __future__ import annotations

from pathlib import Path

from .base import AgentIntegration, RenderedFile


class ClaudeIntegration(AgentIntegration):
    key = "claude"
    display_name = "Claude Code"
    invoke_style = "Claude Code slash skills under .claude/skills/proofsignal-spec-*; invoke as /proofsignal-spec-*"

    def render_files(self, project: Path) -> list[RenderedFile]:
        files = [
            RenderedFile("CLAUDE.md", _context(), "claude/context", "context"),
        ]
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
    return """# ProofSignal Spec Agent Guidance

Use `proofsignal-spec` commands from the target repository root. Keep generated
project artifacts and guidance in English. Store ProofSignal Spec state in
`.proofsignal/`. Do not import private ProofSignal Core packages.

Avoid sensitive files by default and ask before reading local environment files
or secret-bearing configuration. Never persist credential values.
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
            "Gather the target behavior, then run `proofsignal-spec author <alias> \"<description>\"`. Keep one use case mapped to one run request and write reusable skills under `.proofsignal/skills/`.",
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
            "Run `proofsignal-spec validate <alias> --runtime-readiness` when runtime readiness matters, then summarize Core findings without exposing secret values.",
        ),
        "run": (
            "run a registered use case",
            "<alias> [normal|debug]",
            "Run `proofsignal-spec run <alias> --profile normal` unless the user requests `debug`. If required runtime inputs are missing, ask only for the missing values and never persist credentials.",
        ),
        "repair": (
            "repair invalid or failed use cases",
            "<alias> [report path]",
            "Run `proofsignal-spec repair <alias>` or include `--from-report <path>` when the user provides a report. Present proposed edits for approval before applying changes.",
        ),
    }
    return workflows[name]
