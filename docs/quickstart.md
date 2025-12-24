# Quick Start

Get up and running with AgentHelm in 5 minutes.

## Installation

```bash
pip install agenthelm
```

## 1. Initialize Configuration

```bash
agenthelm init
```

This creates `~/.agenthelm/config.yaml` with default settings.

## 2. Set Your API Key

```bash
# Set via config
agenthelm config set api_keys.mistral your-api-key

# Or use environment variable
export MISTRAL_API_KEY="your-api-key"
```

## 3. Run Your First Task

```bash
agenthelm run "What is the capital of France?"
```

Output:

```
Running task: What is the capital of France?
Model: mistral/mistral-large-latest, Max iterations: 10

✓ Success
Paris is the capital of France.

─── Summary ───
Tokens: 156 (120 in / 36 out)
```

## 4. Try Interactive Chat

```bash
agenthelm chat
```

```
AgentHelm Chat (model: mistral/mistral-large-latest)
Type 'exit' or 'quit' to end the session

> Explain quantum computing in simple terms
Quantum computing uses quantum bits (qubits) that can exist in multiple 
states simultaneously, allowing quantum computers to process many 
possibilities at once...

> exit
```

## 5. Create and Execute Plans

```bash
# Generate a plan
agenthelm plan "Build a todo app with Flask" -o plan.yaml

# Execute the plan
agenthelm execute plan.yaml
```

## Next Steps

- [CLI Reference](cli.md) - All commands and options
- [Agents](agents.md) - ToolAgent and PlannerAgent
- [Orchestration](orchestration.md) - Multi-agent workflows
- [MCP Integration](mcp.md) - Connect to MCP servers

## Python SDK

```python
import dspy
from agenthelm import ToolAgent, tool

# Define a tool
@tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

# Create and run agent
lm = dspy.LM("mistral/mistral-large-latest")
agent = ToolAgent(name="calculator", lm=lm, tools=[add])
result = agent.run("What is 2 + 2?")

print(result.answer)  # "4"
```
