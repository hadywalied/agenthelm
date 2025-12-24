"""Tests for agenthelm.mcp - MCP integration."""

import pytest

from agenthelm.mcp import MCPClient, MCPToolAdapter
from agenthelm.core.tool import TOOL_REGISTRY


class TestMCPClient:
    """Tests for MCPClient."""

    def test_init(self):
        """Can create client with config."""
        client = MCPClient({"command": "uvx", "args": ["mcp-server-time"]})
        assert client.server_config["command"] == "uvx"


class TestMCPToolAdapter:
    """Tests for MCPToolAdapter."""

    def test_init_without_compensations(self):
        """Can create adapter without compensations."""
        adapter = MCPToolAdapter({"command": "test"})
        assert adapter._compensations == {}

    def test_init_with_compensations(self):
        """Can create adapter with compensations."""
        adapter = MCPToolAdapter(
            {"command": "test"}, compensations={"create": "delete"}
        )
        assert adapter._compensations["create"] == "delete"

    @pytest.mark.asyncio
    async def test_get_tools_registers_in_registry(self):
        """get_tools registers tools in TOOL_REGISTRY."""
        adapter = MCPToolAdapter({"command": "test"})

        # Mock the tools list
        adapter._tools = [
            {"name": "test_tool", "description": "A test tool", "inputSchema": {}}
        ]

        tools = adapter.get_tools()

        assert len(tools) == 1
        assert tools[0].__name__ == "test_tool"
        assert "test_tool" in TOOL_REGISTRY

    @pytest.mark.asyncio
    async def test_get_tools_includes_compensation(self):
        """get_tools sets compensating_tool from mapping."""
        adapter = MCPToolAdapter(
            {"command": "test"}, compensations={"create_file": "delete_file"}
        )
        adapter._tools = [
            {"name": "create_file", "description": "Create", "inputSchema": {}}
        ]

        adapter.get_tools()

        contract = TOOL_REGISTRY["create_file"]["contract"]
        assert contract["compensating_tool"] == "delete_file"
