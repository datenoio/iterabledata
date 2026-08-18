"""Tests for IterableData MCP server."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import iterable

ROOT = Path(__file__).resolve().parents[1]


class TestMCPServer:
    def test_create_mcp_server_import_error(self):
        with patch.dict("sys.modules", {"mcp": None, "mcp.server": None, "mcp.server.fastmcp": None}):
            from iterable.mcp import server

            with pytest.raises(ImportError, match="mcp package"):
                server.create_mcp_server()

    def test_create_mcp_server_registers_tools(self):
        pytest.importorskip("mcp")
        from iterable.mcp.server import create_mcp_server

        mcp = create_mcp_server("test-iterable")
        assert mcp is not None
        # FastMCP stores tools internally
        tool_manager = getattr(mcp, "_tool_manager", None) or getattr(mcp, "tools", None)
        if tool_manager is not None and hasattr(tool_manager, "tools"):
            names = set(tool_manager.tools.keys())
            assert "detect_format" in names
            assert "read_sample" in names

    def test_register_tools_callable(self):
        mock_mcp = MagicMock()

        from iterable.mcp.server import _register_tools

        _register_tools(mock_mcp)
        assert mock_mcp.tool.call_count >= 6

    def test_server_json_manifest_matches_package(self):
        manifest = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
        schema = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"
        assert manifest["$schema"] == schema
        assert manifest["name"] == "io.github.datenoio/iterabledata"
        assert len(manifest["description"]) <= 100
        assert manifest["version"] == iterable.__version__
        package = manifest["packages"][0]
        assert package["registryType"] == "pypi"
        assert package["identifier"] == "iterabledata"
        assert package["version"] == iterable.__version__
        assert package["transport"]["type"] == "stdio"

    def test_readme_declares_mcp_registry_name(self):
        manifest = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
        marker = f"<!-- mcp-name: {manifest['name']} -->"
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        assert marker in readme

    def test_release_workflow_publishes_mcp_registry(self):
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        assert "mcp-publisher login github-oidc" in workflow
        assert "mcp-publisher publish" in workflow
        assert "waiting for PyPI to index the new version" in workflow
        assert "id-token: write" in workflow
