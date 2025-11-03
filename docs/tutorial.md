# Tutorial: Building Your First Agent with AgentHelm

This tutorial will guide you through building a simple agent using AgentHelm, demonstrating its core features like tool definition, human approval, and rollbacks.

## 1. Setup Your Environment

First, ensure you have Python 3.12+ and a virtual environment set up. Install AgentHelm:

```bash
pip install agenthelm
```

Also, make sure you have your LLM API key set as an environment variable (e.g., `export MISTRAL_API_KEY="your_key_here"`).

## 2. Define Your Tools

Create a file named `my_agent_tools.py`. This file will contain the tools your agent can use.

### Simple Tool: `get_weather`

Let's start with a simple tool to get weather information. AgentHelm's `@tool` decorator automatically infers the tool's contract from your function's type hints.

```python
# my_agent_tools.py
from orchestrator import tool

@tool()
def get_weather(city: str) -> str:
    """Gets the current weather for a given city."""
    # In a real scenario, this would call a weather API
    if city == "New York":
        return "It is 24°C and sunny in New York."
    elif city == "London":
        return "It is 15°C and cloudy in London."
    else:
        return f"Sorry, I don't know the weather for {city}."
```

### Tool Requiring Human Approval: `send_email`

For sensitive actions, you can require human approval. AgentHelm will pause the agent's execution and prompt the user for confirmation.

```python
# my_agent_tools.py (continued)

@tool(requires_approval=True)
def send_email(recipient: str, subject: str, body: str) -> dict:
    """Sends an email to a specified recipient."""
    # In a real scenario, this would integrate with an email service
    print(f"[ACTION REQUIRED] Sending email to {recipient} with subject '{subject}' and body: '{body}'")
    return {"status": "email_sent", "recipient": recipient}
```

### Tool with Rollback: `create_resource` and `delete_resource`

AgentHelm supports transactional workflows with automatic rollbacks. If a multi-step process fails, it can execute compensating actions to undo previous steps.

```python
# my_agent_tools.py (continued)

@tool()
def delete_resource(resource_id: str) -> dict:
    """Deletes a cloud resource by its ID (compensating action)."""
    print(f"[COMPENSATING ACTION] Deleting resource: {resource_id}")
    return {"status": "resource_deleted", "resource_id": resource_id}

@tool(compensating_tool='delete_resource')
def create_resource(resource_type: str, config: dict) -> dict:
    """Creates a cloud resource with specified type and configuration."""
    # In a real scenario, this would call a cloud provider API
    resource_id = f"res-{resource_type}-{hash(str(config))}"
    print(f"[ACTION] Creating resource {resource_id} of type {resource_type} with config {config}")
    return {"status": "resource_created", "resource_id": resource_id}

@tool()
def deploy_application(resource_id: str, app_name: str) -> dict:
    """Deploys an application to a given resource. Designed to fail for demonstration."""
    print(f"[ACTION] Deploying application {app_name} to {resource_id}")
    raise RuntimeError("Deployment failed due to an unexpected error!")
```

## 3. Run Your Agent

Now, let's run the agent using the `agenthelm` CLI. Make sure you are in the directory containing `my_agent_tools.py`.

### Simple Task

```bash
agenthelm run \
  --agent-file my_agent_tools.py \
  --task "What is the weather in London?"
```

### Task Requiring Approval

```bash
agenthelm run \
  --agent-file my_agent_tools.py \
  --task "Send an email to user@example.com with subject 'Hello' and body 'This is a test email.'"
```

When you run this, the agent will pause and ask for your approval before sending the email.

### Task with Rollback

Let's simulate a multi-step workflow where a later step fails, triggering a rollback.

```bash
agenthelm run \
  --agent-file my_agent_tools.py \
  --task "First, create a 'web_server' resource with config {'size': 'medium'}. Then, deploy 'my-app' to it."
```

In this scenario, the `create_resource` tool will succeed, but `deploy_application` will fail. AgentHelm will then automatically call `delete_resource` (the compensating tool) to undo the `create_resource` action.

## 4. Inspect the Trace

After each run, AgentHelm generates a `cli_trace.json` file in your current directory. This file contains a detailed, structured log of every action the agent took, including LLM reasoning, tool inputs/outputs, and any errors or rollbacks.

Open `cli_trace.json` in a text editor to see the full observability in action.

## Next Steps

-   Explore the [Core Concepts](concepts.md) to understand the architecture.
-   Refer to the [API Reference](api_reference.md) for detailed usage of classes and functions.