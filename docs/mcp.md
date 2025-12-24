# MCP Integration

AgentHelm integrates with the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) to connect agents to
external tools and data sources.

## Quick Start

```python
import asyncio
from agenthelm import MCPToolAdapter, ToolAgent
import dspy

lm = dspy.LM("mistral/mistral-large-latest")

async def main():
    # Connect to an MCP server
    adapter = MCPToolAdapter(
        server_config={"command": "uvx", "args": ["mcp-server-time"]}
    )
    await adapter.connect()
    
    # Get tools from MCP server
    tools = adapter.get_tools()
    
    # Use with AgentHelm agents
    agent = ToolAgent(name="time_agent", lm=lm, tools=tools)
    result = agent.run("What time is it?")
    print(result.answer)
    
    await adapter.close()

asyncio.run(main())
```

## MCPToolAdapter

Wraps MCP server tools as AgentHelm-compatible callables.

```python
from agenthelm import MCPToolAdapter

adapter = MCPToolAdapter(
    server_config={
        "command": "uvx",
        "args": ["mcp-server-filesystem", "/path/to/files"],
        "env": {"DEBUG": "true"},  # Optional
    }
)

await adapter.connect()
tools = adapter.get_tools()
```

### Server Config

| Key       | Description                                      |
|-----------|--------------------------------------------------|
| `command` | Executable to run (e.g., `uvx`, `npx`, `python`) |
| `args`    | Command arguments                                |
| `env`     | Environment variables (optional)                 |

## Saga Support

Define compensating actions for MCP tools:

```python
adapter = MCPToolAdapter(
    server_config={"command": "uvx", "args": ["mcp-server-files"]},
    compensations={
        "create_file": "delete_file",
        "write_file": "restore_file",
    }
)
```

On failure, the Orchestrator will run the compensating MCP tool.

## MCPClient (Low-Level)

For direct MCP protocol access:

```python
from agenthelm import MCPClient

client = MCPClient({"command": "uvx", "args": ["mcp-server-time"]})
await client.connect()

# List available tools
tools = await client.list_tools()

# Call a tool
result = await client.call_tool("get_time", {"timezone": "UTC"})

await client.close()
```

## Example: File Operations Agent

```python
adapter = MCPToolAdapter(
    server_config={"command": "uvx", "args": ["mcp-server-filesystem", "."]},
    compensations={"write_file": "delete_file"}
)
await adapter.connect()

agent = ToolAgent(
    name="file_agent",
    lm=lm,
    tools=adapter.get_tools(),
    role="You are a file management assistant."
)

result = agent.run("Create a new file called notes.txt with 'Hello World'")
```

## API Reference

::: agenthelm.MCPToolAdapter
options:
show_source: false

::: agenthelm.MCPClient
options:
show_source: false
