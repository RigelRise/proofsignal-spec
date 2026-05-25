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
