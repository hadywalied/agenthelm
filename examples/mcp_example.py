"""
MCP Integration Example

Demonstrates connecting to MCP servers and using their tools.
"""

import asyncio
import dspy
from agenthelm import MCPToolAdapter, ToolAgent


async def main():
    # Configure LLM
    lm = dspy.LM("mistral/mistral-large-latest")

    # Connect to an MCP server (example: time server)
    # To run this example, you need: uvx mcp-server-time
    mcp_command = ["uvx", "mcp-server-time"]

    print(f"Connecting to MCP server: {' '.join(mcp_command)}")

    async with MCPToolAdapter(command=mcp_command) as adapter:
        # List available tools
        tools = await adapter.get_tools()
        print(f"\nAvailable MCP tools: {len(tools)}")
        for tool in tools:
            print(f"  - {tool.__name__}: {tool.__doc__}")

        # Create agent with MCP tools
        agent = ToolAgent(
            name="mcp_agent",
            lm=lm,
            tools=tools,
            max_iters=3,
        )

        # Run a task using MCP tools
        task = "What is the current time?"
        print(f"\nTask: {task}")

        result = agent.run(task)

        if result.success:
            print(f"✓ Answer: {result.answer}")
        else:
            print(f"✗ Error: {result.error}")


if __name__ == "__main__":
    print("MCP Integration Example")
    print("=" * 50)
    print("\nNote: This example requires an MCP server.")
    print("Install with: pip install mcp")
    print("Run server with: uvx mcp-server-time")
    print()

    try:
        asyncio.run(main())
    except FileNotFoundError:
        print("Error: MCP server not found. Install with: pip install mcp")
    except Exception as e:
        print(f"Error: {e}")
