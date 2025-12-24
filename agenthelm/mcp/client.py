"""MCPClient - Low-level MCP protocol client."""

import os
from typing import Any

from mcp import StdioServerParameters, stdio_client, ClientSession


class MCPClient:
    """
    Low-level MCP protocol client.

    Note: On Windows, MCP stdio transport may have issues with subprocess
    buffering and pipe handling. Using PYTHONUNBUFFERED=1 can help.
    """

    def __init__(self, server_config: dict):
        """
        Initialize MCP client.

        Args:
            server_config: Dict with 'command', 'args', and optional 'env'
                Example: {"command": "uvx", "args": ["mcp-server-time"]}
        """
        self.server_config = server_config
        self._session: ClientSession | None = None
        self._context = None
        self._read = None
        self._write = None

    async def connect(self):
        """Connect to the MCP server."""
        # Build environment with unbuffered Python (helps on Windows)
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        if self.server_config.get("env"):
            env.update(self.server_config["env"])

        params = StdioServerParameters(
            command=self.server_config["command"],
            args=self.server_config.get("args", []),
            env=env,
        )

        # Store the context manager to properly close it later
        self._context = stdio_client(params)
        self._read, self._write = await self._context.__aenter__()
        self._session = ClientSession(self._read, self._write)
        await self._session.initialize()

    async def list_tools(self) -> list[dict]:
        """List available tools from the MCP server."""
        if not self._session:
            raise RuntimeError("Not connected. Call connect() first.")
        result = await self._session.list_tools()
        return [tool.model_dump() for tool in result.tools]

    async def call_tool(self, name: str, arguments: dict) -> Any:
        """Call a tool on the MCP server."""
        if not self._session:
            raise RuntimeError("Not connected. Call connect() first.")
        result = await self._session.call_tool(name, arguments)
        return result.content

    async def close(self):
        """Close the connection and clean up resources."""
        self._session = None
        if self._context:
            try:
                await self._context.__aexit__(None, None, None)
            except Exception:
                pass  # Ignore cleanup errors
            self._context = None
        self._read = None
        self._write = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
