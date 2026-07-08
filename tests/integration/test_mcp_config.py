from __future__ import annotations

import json

from helpers import CliTestCase

from verifysignal_spec.integrations.mcp import PLAYWRIGHT_MCP_SERVER, merge_mcp_servers


def _read_mcp(project) -> dict:
    return json.loads((project / ".mcp.json").read_text(encoding="utf-8"))


def test_merge_creates_mcp_json_when_absent(tmp_path) -> None:
    result = merge_mcp_servers(tmp_path, {"playwright": PLAYWRIGHT_MCP_SERVER})

    assert result["skipped"] is False
    assert "playwright" in result["added"]
    data = _read_mcp(tmp_path)
    assert data["mcpServers"]["playwright"]["command"] == "npx"
    assert data["mcpServers"]["playwright"]["args"] == ["-y", "@playwright/mcp@latest"]


def test_merge_preserves_unrelated_servers(tmp_path) -> None:
    (tmp_path / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"foo": {"command": "foo-server"}}}), encoding="utf-8"
    )

    result = merge_mcp_servers(tmp_path, {"playwright": PLAYWRIGHT_MCP_SERVER})

    assert result["skipped"] is False
    data = _read_mcp(tmp_path)
    assert "foo" in data["mcpServers"]
    assert "playwright" in data["mcpServers"]
    assert "foo" in result["preserved"]


def test_merge_is_idempotent(tmp_path) -> None:
    merge_mcp_servers(tmp_path, {"playwright": PLAYWRIGHT_MCP_SERVER})
    second = merge_mcp_servers(tmp_path, {"playwright": PLAYWRIGHT_MCP_SERVER})

    assert second["unchanged"] is True
    assert second["added"] == []


def test_merge_does_not_clobber_malformed_file(tmp_path) -> None:
    (tmp_path / ".mcp.json").write_text("{not valid json", encoding="utf-8")

    result = merge_mcp_servers(tmp_path, {"playwright": PLAYWRIGHT_MCP_SERVER})

    assert result["skipped"] is True
    # The user's file is left exactly as-is — we never destroy what we cannot safely merge.
    assert (tmp_path / ".mcp.json").read_text(encoding="utf-8") == "{not valid json"


def test_merge_reports_node_missing_but_still_writes(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("verifysignal_spec.integrations.mcp.shutil.which", lambda _name: None)

    result = merge_mcp_servers(tmp_path, {"playwright": PLAYWRIGHT_MCP_SERVER})

    assert result["nodeAvailable"] is False
    # Config is still written so it is ready the moment Node is installed.
    assert (tmp_path / ".mcp.json").exists()


class McpConfigInstallTest(CliTestCase):
    def test_claude_install_writes_playwright_mcp(self) -> None:
        code, _, err = self.cli(["init", str(self.project), "--integration", "claude", "--json"])
        self.assertEqual(code, 0, err)
        mcp = self.project / ".mcp.json"
        assert mcp.exists()
        data = json.loads(mcp.read_text(encoding="utf-8"))
        assert "playwright" in data["mcpServers"]
        assert data["mcpServers"]["playwright"]["args"] == ["-y", "@playwright/mcp@latest"]

    def test_codex_install_does_not_write_mcp_json(self) -> None:
        code, _, err = self.cli(["init", str(self.project), "--integration", "codex", "--json"])
        self.assertEqual(code, 0, err)
        assert not (self.project / ".mcp.json").exists()
