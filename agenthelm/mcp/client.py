from typing import Any

from mcp import StdioServerParameters, stdio_client, ClientSession


class MCPClient:
    """Low-level MCP protocol client."""

    def __init__(self, server_config: dict):
        """
        server_config example:
        {"command": "uvx", "args": ["mcp-server-time"]}
        """
        self.server_config = server_config

    async def connect(self):
        params = StdioServerParameters(
            command=self.server_config["command"],
            args=self.server_config.get("args", []),
            env=self.server_config.get("env"),
        )
        # stdio_client is a context manager, but we need persistent connection
        self._read, self._write = await stdio_client(params).__aenter__()
        self._session = ClientSession(self._read, self._write)
        await self._session.initialize()

    async def list_tools(self) -> list[dict]:
        if not self._session:
            raise RuntimeError("Not connected")
        result = await self._session.list_tools()
        return [tool.model_dump() for tool in result.tools]

    async def call_tool(self, name: str, arguments: dict) -> Any:
        if not self._session:
            raise RuntimeError("Not connected")
        result = await self._session.call_tool(name, arguments)
        return result.content

    async def close(self):
        if self._session:
            # Clean up resources
            self._session = None
