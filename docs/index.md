![image](assets/logo_h.svg)
---

# AgentHelm

**Production-Ready Orchestration for AI Agents.**

AgentHelm is a lightweight Python framework for building AI agents with a focus on production-readiness. Built on DSPy,
it provides the essential orchestration layer to make your agents observable, reliable, and safe.

## Why AgentHelm?

In the rapidly evolving world of AI agents, many frameworks focus on rapid prototyping. AgentHelm is different—it's
built for **production environments** where you need:

- 🔍 **Full observability** of every tool call
- 🛡️ **Human-in-the-loop** approval for sensitive actions
- 🔄 **Automatic rollbacks** when things go wrong
- 📊 **Cost tracking** and token usage monitoring

## Installation

```bash
pip install agenthelm
```

## Quick Start

### CLI

```bash
# Initialize configuration
agenthelm init

# Run a simple task
agenthelm run "What is the capital of France?"

# Interactive chat
agenthelm chat

# Generate a plan
agenthelm plan "Build a web scraper" -o plan.yaml

# Execute the plan
agenthelm execute plan.yaml
```

### Python SDK

```python
import dspy
from agenthelm import ToolAgent, tool

# Define a tool
@tool()
def get_weather(city: str) -> str:
    """Gets the current weather for a given city."""
    if city == "New York":
        return "It is 24°C and sunny in New York."
    return f"Weather data not available for {city}."

# Create agent
lm = dspy.LM("mistral/mistral-large-latest")
agent = ToolAgent(name="weather_bot", lm=lm, tools=[get_weather])

# Run task
result = agent.run("What's the weather in New York?")
print(result.answer)
```

## Key Features

### 🔧 Tool Decorator

```python
@tool()
def search(query: str) -> str:
    """Search the web."""
    return f"Results for: {query}"

@tool(requires_approval=True)
def send_email(to: str, body: str) -> dict:
    """Send an email (requires approval)."""
    return {"status": "sent"}
```

### 📊 Observability

```bash
# View execution traces
agenthelm traces list

# Filter by status
agenthelm traces filter --status failed

# Export to Markdown
agenthelm traces export -o report.md -f md
```

### 🔗 MCP Integration

```bash
# Connect to MCP servers
agenthelm mcp list-tools uvx mcp-server-time
agenthelm mcp run uvx mcp-server-time -t "What time is it?"
```

### 🔄 Plan-Driven Execution

```bash
# Generate a multi-step plan
agenthelm plan "Build a todo app" -o plan.yaml

# Review and execute
agenthelm execute plan.yaml
```

## Next Steps

- [Quick Start Guide](quickstart.md) - Get running in 5 minutes
- [CLI Reference](cli.md) - All commands and options
- [Agents](agents.md) - ToolAgent and PlannerAgent
- [Orchestration](orchestration.md) - Multi-agent workflows

## License

MIT License - See [LICENSE](https://github.com/hadywalied/agenthelm/blob/main/LICENSE) for details.