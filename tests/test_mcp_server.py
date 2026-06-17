"""Tests for IterableData MCP server."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


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
