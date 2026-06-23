"""Host-agent MCP-server configuration.

ProofSignal ships zero inference; the host agent (e.g. Claude Code) is the brain. To make live
authoring frictionless, integrations may declare MCP servers that `integration install` merges into
the agent's project-scoped MCP config. For Claude Code that config is a project-root ``.mcp.json``.

The merge is SAFE by construction: it preserves the user's other servers, is idempotent, and never
clobbers a file it cannot parse. Consent is not bypassed — Claude Code itself prompts the user to
approve a project-scoped server before first use.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from proofsignal_spec.workspace.repository import save_document

# Canonical Playwright MCP server entry. `-y` auto-confirms the npx package install.
PLAYWRIGHT_MCP_SERVER: dict[str, Any] = {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@playwright/mcp@latest"],
}


def node_available() -> bool:
    """True when `npx` is on PATH (the Playwright MCP runs via `npx @playwright/mcp`)."""
    return shutil.which("npx") is not None


def merge_mcp_servers(project: Path, servers: dict[str, Any]) -> dict[str, Any]:
    """Merge ``servers`` into ``<project>/.mcp.json`` under the ``mcpServers`` key.

    Preserves existing servers, only writes when something changed (idempotent), and skips (leaving
    the file untouched) when an existing ``.mcp.json`` is not safely mergeable. Returns a status dict.
    """

    path = project / ".mcp.json"
    status: dict[str, Any] = {
        "path": ".mcp.json",
        "added": [],
        "updated": [],
        "preserved": [],
        "unchanged": False,
        "skipped": False,
        "nodeAvailable": node_available(),
    }

    existing: Any = {}
    if path.exists():
        # Parse strictly as JSON. If it is not valid JSON (or not an object), do NOT overwrite the
        # user's file — surface a skip so the caller can warn instead of destroying their config.
        try:
            existing = json.loads(path.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            status["skipped"] = True
            status["reason"] = "existing .mcp.json is not valid JSON; left untouched"
            return status
        if not isinstance(existing, dict):
            status["skipped"] = True
            status["reason"] = "existing .mcp.json is not a JSON object; left untouched"
            return status

    current_servers = existing.get("mcpServers", {})
    if not isinstance(current_servers, dict):
        status["skipped"] = True
        status["reason"] = "existing .mcp.json `mcpServers` is not an object; left untouched"
        return status

    merged = dict(current_servers)
    for name, spec in servers.items():
        if name not in merged:
            status["added"].append(name)
        elif merged[name] != spec:
            status["updated"].append(name)
        merged[name] = spec
    status["preserved"] = [name for name in current_servers if name not in servers]

    if merged == current_servers:
        status["unchanged"] = True
        return status

    new_doc = dict(existing)
    new_doc["mcpServers"] = merged
    save_document(path, new_doc)
    return status
