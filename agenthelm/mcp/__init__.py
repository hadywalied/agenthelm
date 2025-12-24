"""
AgentHelm MCP Integration - Connect to MCP servers.

Example:
    from agenthelm.mcp import MCPToolAdapter

    adapter = MCPToolAdapter(
        server_config={"command": "uvx", "args": ["mcp-server-time"]},
        compensations={"create_file": "delete_file"}
    )
    await adapter.connect()

    tools = adapter.get_tools()
    agent = ToolAgent(name="mcp_agent", lm=lm, tools=tools)
"""

from agenthelm.mcp.client import MCPClient
from agenthelm.mcp.adapter import MCPToolAdapter

__all__ = [
    "MCPClient",
    "MCPToolAdapter",
]
