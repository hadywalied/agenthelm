"""MCPToolAdapter - Wrap MCP server tools as AgentHelm tools."""

import asyncio
from typing import Callable, Any

from agenthelm import TOOL_REGISTRY
from agenthelm.mcp.client import MCPClient


class MCPToolAdapter:
    """
    Wraps MCP server tools as AgentHelm-compatible callables.

    Example:
        adapter = MCPToolAdapter({"command": "uvx", "args": ["mcp-server-time"]})
        await adapter.connect()
        tools = adapter.get_tools()
    """

    def __init__(
        self,
        server_config: dict,
        compensations: dict[str, str] | None = None,
    ):
        self._client = MCPClient(server_config)
        self._tools: list[dict] = []
        self._compensations = compensations or {}

    async def connect(self):
        """Connect and discover tools."""
        await self._client.connect()
        self._tools = await self._client.list_tools()

    def get_tools(self) -> list[Callable]:
        """
        Return MCP tools as callable functions.

        Registers each tool in TOOL_REGISTRY with compensation info.
        """
        callables = []
        for tool_info in self._tools:
            name = tool_info["name"]
            description = tool_info.get("description", "MCP tool")

            # Create wrapper function
            def make_tool_func(tool_name: str):
                def tool_func(**kwargs) -> Any:
                    """Sync wrapper for async MCP call."""
                    # Bridge async -> sync for DSPy compatibility
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If already in async context, use run_coroutine_threadsafe

                        future = asyncio.run_coroutine_threadsafe(
                            self._client.call_tool(tool_name, kwargs), loop
                        )
                        return future.result(timeout=30)
                    else:
                        return asyncio.run(self._client.call_tool(tool_name, kwargs))

                return tool_func

            func = make_tool_func(name)
            func.__name__ = name
            func.__doc__ = description

            # Register in TOOL_REGISTRY with compensation
            compensate = self._compensations.get(name)
            TOOL_REGISTRY[name] = {
                "function": func,
                "contract": {
                    "inputs": self._extract_input_schema(tool_info),
                    "outputs": {"result": "Any"},
                    "compensating_tool": compensate,
                    "tags": ["mcp"],
                },
            }

            callables.append(func)
        return callables

    def _extract_input_schema(self, tool_info: dict) -> dict:
        """Extract input parameters from MCP tool schema."""
        input_schema = tool_info.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        return {k: v.get("type", "string") for k, v in properties.items()}

    async def close(self):
        await self._client.close()
