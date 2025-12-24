# Orchestration

AgentHelm's orchestration layer executes plans by routing steps to registered agents.

## Quick Start

```python
import asyncio
from agenthelm import (
    AgentRegistry, Orchestrator, PlannerAgent, ToolAgent, tool
)
import dspy

lm = dspy.LM("openai/gpt-4o-mini")

# Define tools
@tool()
def search(query: str) -> str:
    """Search for information."""
    return f"Results for: {query}"

@tool()
def write(content: str) -> str:
    """Write content to file."""
    return f"Wrote: {content}"

# Create and register agents
registry = AgentRegistry()
registry.register(ToolAgent(name="researcher", lm=lm, tools=[search]))
registry.register(ToolAgent(name="writer", lm=lm, tools=[write]))

# Generate a plan
planner = PlannerAgent(name="planner", lm=lm, tools=[search, write])
plan = planner.plan("Research AI trends and write a summary")

# Review and approve
print(plan.to_yaml())
plan.approved = True

# Execute
orchestrator = Orchestrator(registry)
result = asyncio.run(orchestrator.execute(plan))
print(result.answer)
```

## AgentRegistry

Container for named agents that can be looked up during orchestration.

```python
from agenthelm import AgentRegistry

registry = AgentRegistry()

# Register agents
registry.register(researcher_agent)  # Uses agent.name as key
registry.register(writer_agent)

# Lookup
agent = registry["researcher"]
agent = registry.get("researcher")  # Returns None if not found

# Check membership
if "researcher" in registry:
    ...

# Iterate
for name in registry:
    print(name)

# Properties
registry.names  # ["researcher", "writer"]
len(registry)   # 2

# Management
registry.unregister("researcher")
registry.clear()
```

## Orchestrator

Executes approved plans by routing steps to agents.

```python
from agenthelm import Orchestrator

orchestrator = Orchestrator(
    registry=registry,
    default_agent=fallback_agent  # Optional: for steps without agent_name
)

# Execute a plan (async)
result = await orchestrator.execute(plan)
```

### Execution Flow

```
Plan.get_ready_steps()
        │
        ▼
┌───────────────────┐
│  Parallel Batch   │  Steps with no pending dependencies
│  (asyncio.gather) │  run concurrently
└───────────────────┘
        │
        ▼
   Mark completed
        │
        ▼
   Next batch...
        │
        ▼
    AgentResult
```

### Parallel Execution

Steps without dependencies run in parallel:

```python
plan = Plan(
    goal="Research and summarize",
    approved=True,
    steps=[
        PlanStep(id="a", agent_name="researcher", description="Search topic A"),
        PlanStep(id="b", agent_name="researcher", description="Search topic B"),
        PlanStep(id="c", agent_name="writer", description="Combine results",
                 depends_on=["a", "b"]),  # Waits for a and b
    ]
)

# Steps a and b run in parallel
# Step c runs after both complete
```

### Error Handling

Failed steps are marked and tracked:

```python
result = await orchestrator.execute(plan)

if not result.success:
    failed = [s for s in plan.steps if s.status == StepStatus.FAILED]
    for step in failed:
        print(f"Step {step.id} failed: {step.error}")
```

## Plan Approval Flow

Plans must be approved before execution:

```python
# Generate plan
plan = planner.plan("Do something complex")

# Review (CLI or programmatic)
print(plan.to_yaml())

# Approve
plan.approved = True

# Execute
result = await orchestrator.execute(plan)
```

### CLI Approval (Week 5)

```bash
$ agenthelm plan "Research AI trends" --approve
```

## Default Agent

For steps without `agent_name`, a default agent can be used:

```python
default = ToolAgent(name="default", lm=lm, tools=[...])
orchestrator = Orchestrator(registry, default_agent=default)

# This step uses default_agent
PlanStep(id="step_1", tool_name="search", description="...")
```

## Saga Pattern (Rollback on Failure)

AgentHelm supports the Saga pattern for compensating actions when steps fail.

### How It Works

1. Steps execute normally
2. If a step fails, **rollback** runs for completed steps in reverse order
3. Each completed step's compensating action is called

### Defining Compensating Actions

**Option 1: Per-Tool (default)**

```python
@tool(compensating_tool="delete_file")
def create_file(path: str) -> str:
    """Create a file. Rollback: delete it."""
    ...
```

**Option 2: Per-Step (override)**

```python
PlanStep(
    id="step_1",
    tool_name="create_file",
    args={"path": "/tmp/data.txt"},
    compensate_tool="archive_file",  # Overrides tool default
    compensate_args={"path": "/tmp/data.txt"},
)
```

### Enabling Rollback

```python
# Rollback enabled by default
orchestrator = Orchestrator(registry, enable_rollback=True)

# Disable if needed
orchestrator = Orchestrator(registry, enable_rollback=False)
```

### Example

```python
plan = Plan(
    goal="Create and send report",
    approved=True,
    steps=[
        PlanStep(
            id="create",
            agent_name="writer",
            tool_name="create_report",
            description="Create report file",
            compensate_tool="delete_report",  # Rollback action
        ),
        PlanStep(
            id="send",
            agent_name="sender",
            tool_name="send_email",
            description="Send report via email",
            depends_on=["create"],
        ),
    ],
)

# If "send" fails, "create" is rolled back via delete_report
result = await orchestrator.execute(plan)
```

## API Reference

::: agenthelm.AgentRegistry
options:
show_source: false

::: agenthelm.Orchestrator
options:
show_source: false
