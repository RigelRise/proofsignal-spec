from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RenderedFile:
    path: str
    content: str
    source: str
    kind: str = "agent-skill"


class AgentIntegration:
    key: str
    display_name: str
    invoke_style: str

    def render_files(self, project: Path) -> list[RenderedFile]:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class WorkflowCommandSpec:
    stage: str
    description: str
    argument_hint: str = ""

    @property
    def canonical_name(self) -> str:
        return f"proofsignal.{self.stage}"

    @property
    def skill_name(self) -> str:
        return f"proofsignal-{self.stage}"


WORKFLOW_COMMANDS = [
    WorkflowCommandSpec("understand", "Capture repository and product context before use case authoring", "[alias or goal]"),
    WorkflowCommandSpec("specify", "Define one browser validation use case", '<alias> "<behavior>"'),
    WorkflowCommandSpec("clarify", "Resolve high-impact unknowns", "<alias>"),
    WorkflowCommandSpec("plan", "Plan one run request and reusable skills", "<alias>"),
    WorkflowCommandSpec("tasks", "Generate ordered authoring tasks", "<alias>"),
    WorkflowCommandSpec("implement", "Create or update planned artifacts", "<alias>"),
    WorkflowCommandSpec("validate", "Validate draft artifacts through ProofSignal Spec/Core", "<alias>"),
    WorkflowCommandSpec("list", "List registered use cases and workflow state", ""),
    WorkflowCommandSpec("run", "Run a selected validated use case", "<alias>"),
    WorkflowCommandSpec("repair", "Repair invalid or failed use cases", "<alias> [report path]"),
]


def load_agent_command_template(stage: str) -> str:
    path = Path(__file__).resolve().parents[1] / "templates" / "agent-commands" / f"proofsignal.{stage}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    else:
        return f"# proofsignal.{stage}\n\nFollow the ProofSignal workflow stage rules.\n"


def render_workflow_skill(spec: WorkflowCommandSpec, agent: str, include_argument_hint: bool = False) -> str:
    body = load_agent_command_template(spec.stage)
    hint = spec.argument_hint.replace('"', '\\"')
    argument = f'argument-hint: "{hint}"\n' if include_argument_hint and spec.argument_hint else ""
    return f"""---
name: "{spec.skill_name}"
description: "{agent} workflow command for {spec.canonical_name}: {spec.description}"
{argument}---

# {spec.skill_name}

Invoke this command as `/{spec.skill_name}`.

{body}
"""


def render_workflow_skill_files(root: str, agent: str, include_argument_hint: bool = False) -> list[RenderedFile]:
    return [
        RenderedFile(
            f"{root}/{spec.skill_name}/SKILL.md",
            render_workflow_skill(spec, agent, include_argument_hint=include_argument_hint),
            f"{agent.lower()}/{spec.skill_name}",
        )
        for spec in WORKFLOW_COMMANDS
    ]
