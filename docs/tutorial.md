# Tutorial: Building Your First Agent

This tutorial guides you through building a simple agent using AgentHelm.

## 1. Setup

```bash
pip install agenthelm
agenthelm init
```

Set your API key:

```bash
export MISTRAL_API_KEY="your_key_here"
# or
agenthelm config set api_keys.mistral your_key_here
```

## 2. Define Your Tools

Create a file named `my_tools.py`:

```python
# my_tools.py
from agenthelm import tool

@tool()
def get_weather(city: str) -> str:
    """Gets the current weather for a given city."""
    if city == "New York":
        return "It is 24°C and sunny in New York."
    elif city == "London":
        return "It is 15°C and cloudy in London."
    return f"Weather data not available for {city}."

@tool(requires_approval=True)
def send_email(recipient: str, subject: str, body: str) -> dict:
    """Sends an email to a specified recipient."""
    print(f"Sending email to {recipient}")
    return {"status": "sent", "recipient": recipient}
```

## 3. Run Your Agent

### Simple Task

```bash
agenthelm run "What is the weather in London?" \
  --tools my_tools:get_weather
```

### Interactive Mode

```bash
agenthelm chat --tools my_tools:get_weather,send_email
```

### Task Requiring Approval

```bash
agenthelm run "Send an email to user@example.com" \
  --tools my_tools:send_email
```

The agent will pause and ask for your approval.

## 4. View Traces

After running, view your execution traces:

```bash
# List recent traces
agenthelm traces list

# Show trace details
agenthelm traces show 0

# Filter by tool
agenthelm traces filter --tool get_weather

# Export to Markdown
agenthelm traces export -o report.md -f md
```

## 5. Using the Python SDK

```python
import dspy
from agenthelm import ToolAgent, tool


@tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


@tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


# Create agent with tools
lm = dspy.LM("mistral/mistral-large-latest")
agent = ToolAgent(
    name="calculator",
    lm=lm,
    tools=[add, multiply],
    max_iters=5,
)

# Run task
result = agent.run("What is 3 + 4, then multiply by 2?")

if result.success:
    print(f"Answer: {result.answer}")
    print(f"Tokens: {result.token_usage.input_tokens + result.token_usage.output_tokens}")
else:
    print(f"Error: {result.error}")
```

## 6. Generate and Execute Plans

```bash
# Generate a plan
agenthelm plan "Build a calculator that can add and multiply" -o plan.yaml

# Review the plan file, then execute
agenthelm execute plan.yaml
```

## Next Steps

- [CLI Reference](cli.md) - All commands and options
- [Core Concepts](concepts.md) - Architecture deep dive
- [Orchestration](orchestration.md) - Multi-agent workflows