# API Reference

Complete API reference for AgentHelm.

## Core

### `@tool` Decorator

```python
from agenthelm import tool

@tool(
    requires_approval=False,  # Human-in-the-loop
    max_retries=0,            # Automatic retries
    timeout=None,             # Execution timeout
    compensating_tool=None,   # Rollback function name
)
def my_tool(arg: str) -> str:
    """Tool description."""
    return result
```

### `TOOL_REGISTRY`

Global registry of all decorated tools.

```python
from agenthelm import TOOL_REGISTRY

# List all registered tools
for name, info in TOOL_REGISTRY.items():
    print(f"{name}: {info['description']}")
```

---

## Agents

### `ToolAgent`

ReAct-style agent that reasons and executes tools.

```python
from agenthelm import ToolAgent

agent = ToolAgent(
    name="my_agent",           # Agent identifier
    lm=lm,                     # DSPy language model
    tools=[tool1, tool2],      # List of tool functions
    memory=None,               # Optional MemoryHub
    tracer=None,               # Optional ExecutionTracer
    role=None,                 # Optional persona description
    max_iters=10,              # Max ReAct iterations
)

result = agent.run("Your task here")
```

### `PlannerAgent`

Generates execution plans from tasks.

```python
from agenthelm import PlannerAgent

planner = PlannerAgent(
    name="my_planner",
    lm=lm,
    tools=[tool1, tool2],
    role=None,
)

plan = planner.plan("Build a web scraper")
print(plan.to_yaml())
```

### `AgentResult`

Result of agent execution.

| Field            | Type          | Description                 |
|------------------|---------------|-----------------------------|
| `success`        | `bool`        | Whether execution succeeded |
| `answer`         | `str`         | Final answer from agent     |
| `error`          | `str`         | Error message if failed     |
| `events`         | `list[Event]` | All tool executions         |
| `total_cost_usd` | `float`       | Estimated total cost        |
| `token_usage`    | `TokenUsage`  | Aggregated token usage      |
| `iterations`     | `int`         | Number of ReAct iterations  |

---

## Orchestration

### `AgentRegistry`

Registry for named agent lookup.

```python
from agenthelm import AgentRegistry

registry = AgentRegistry()
registry.register("researcher", researcher_agent)
registry.register("writer", writer_agent)

agent = registry.get("researcher")
```

### `Orchestrator`

Executes plans by routing steps to agents.

```python
from agenthelm import Orchestrator

orchestrator = Orchestrator(
    registry=registry,
    parallel=True,  # Enable parallel step execution
)

result_plan = orchestrator.execute(plan)
```

---

## Plans

### `Plan`

Execution plan with steps and dependencies.

```python
from agenthelm import Plan, PlanStep

plan = Plan(
    goal="Build a web scraper",
    reasoning="Need to fetch and parse HTML",
    steps=[
        PlanStep(id="step1", tool_name="fetch", description="Fetch page"),
        PlanStep(id="step2", tool_name="parse", description="Parse HTML", depends_on=["step1"]),
    ],
)

# Serialize to YAML
yaml_str = plan.to_yaml()

# Load from YAML
plan = Plan.from_yaml(yaml_str)
```

### `PlanStep`

Single step in a plan.

| Field             | Type         | Description                |
|-------------------|--------------|----------------------------|
| `id`              | `str`        | Unique step identifier     |
| `tool_name`       | `str`        | Tool to execute            |
| `description`     | `str`        | What this step does        |
| `args`            | `dict`       | Tool arguments             |
| `depends_on`      | `list[str]`  | Step IDs this depends on   |
| `status`          | `StepStatus` | Execution status           |
| `agent_name`      | `str`        | Optional agent to route to |
| `compensate_tool` | `str`        | Rollback tool for Saga     |

---

## Tracing

### `ExecutionTracer`

Traces tool executions and saves to storage.

```python
from agenthelm import ExecutionTracer
from agenthelm.core.storage import SqliteStorage

tracer = ExecutionTracer(
    storage=SqliteStorage("traces.db"),
    approval_handler=None,  # Optional ApprovalHandler
)

output, event = tracer.trace_and_execute(my_tool, arg="value")
```

### `Event`

Execution event with full metadata.

| Field                | Type         | Description         |
|----------------------|--------------|---------------------|
| `timestamp`          | `datetime`   | When executed       |
| `tool_name`          | `str`        | Tool name           |
| `inputs`             | `dict`       | Input arguments     |
| `outputs`            | `Any`        | Return value        |
| `execution_time`     | `float`      | Duration in seconds |
| `token_usage`        | `TokenUsage` | Token counts        |
| `estimated_cost_usd` | `float`      | Estimated cost      |
| `error_state`        | `str`        | Error if failed     |

### OpenTelemetry

```python
from agenthelm.tracing import init_tracing, trace_tool, trace_agent

init_tracing(service_name="my-app", otlp_endpoint="http://localhost:4317")

with trace_tool("search", inputs={"q": "AI"}):
    result = search("AI")
```

---

## Storage

### `JsonStorage`

```python
from agenthelm.core.storage import JsonStorage

storage = JsonStorage("traces.json")
storage.save(event)
events = storage.load()
```

### `SqliteStorage`

```python
from agenthelm.core.storage import SqliteStorage

storage = SqliteStorage("traces.db")
storage.save(event)
events = storage.query(tool_name="search", limit=10)
```

---

## Memory

### `MemoryHub`

Central hub for short-term and semantic memory.

```python
from agenthelm import MemoryHub

hub = MemoryHub(
    short_term=InMemoryShortTermMemory(),
    semantic=SemanticMemory(qdrant_url="http://localhost:6333"),
)

# Use with agent
agent = ToolAgent(name="agent", lm=lm, tools=[], memory=hub)
```

### Short-Term Memory

- `InMemoryShortTermMemory` - In-memory dictionary
- `SqliteShortTermMemory` - SQLite-backed

### Semantic Memory

- `SemanticMemory` - Qdrant-backed vector search

---

## Cost Tracking

### `CostTracker`

```python
from agenthelm import get_cost_tracker

tracker = get_cost_tracker()
tracker.record("gpt-4o", input_tokens=500, output_tokens=150)

summary = tracker.get_summary()
# {"total_input_tokens": 500, "total_output_tokens": 150, "total_cost_usd": 0.0055}
```

---

## Approval Handlers

```python
from agenthelm import CliHandler, AutoApproveHandler, AutoDenyHandler

# Interactive CLI approval
tracer = ExecutionTracer(approval_handler=CliHandler())

# Auto-approve (testing)
tracer = ExecutionTracer(approval_handler=AutoApproveHandler())

# Auto-deny (dry-run)
tracer = ExecutionTracer(approval_handler=AutoDenyHandler())
```
