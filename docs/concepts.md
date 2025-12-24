# Core Concepts

This section explains the fundamental ideas behind AgentHelm.

## Tool Contracts

Tools are the building blocks of agent actions. AgentHelm uses a decorator-based approach to define tools with rich
metadata:

```python
from agenthelm import tool

@tool(
    requires_approval=True,  # Human-in-the-loop
    max_retries=3,           # Automatic retries
    timeout=30.0,            # Execution timeout
    tags=["financial", "sensitive"]
)
def charge_credit_card(amount: float, card_id: str) -> dict:
    """Charge a credit card for the specified amount."""
    return {"status": "charged", "transaction_id": "txn_123"}
```

The `@tool` decorator automatically:

- Extracts the function signature and docstring
- Registers the tool in `TOOL_REGISTRY`
- Enables execution tracing and cost tracking

## Execution Tracing

The `ExecutionTracer` records every tool call with rich metadata:

```python
from agenthelm import ExecutionTracer
from agenthelm.core.storage import JsonStorage

tracer = ExecutionTracer(storage=JsonStorage("trace.json"))

# Execute a tool with full tracing
output, event = tracer.trace_and_execute(my_tool, arg1="value", arg2=123)

# Event contains: timestamp, inputs, outputs, duration, token_usage, cost, etc.
```

### Event Model

Every execution produces an `Event` with these fields:

| Field                   | Description                     |
|-------------------------|---------------------------------|
| `timestamp`             | When the event occurred         |
| `tool_name`             | Name of the executed tool       |
| `inputs` / `outputs`    | Arguments and return value      |
| `execution_duration_ms` | How long it took                |
| `token_usage`           | LLM tokens (input/output/model) |
| `estimated_cost_usd`    | Cost estimate based on pricing  |
| `agent_name`            | Which agent executed this       |
| `session_id`            | Session identifier              |
| `trace_id`              | Unique execution ID             |

## Cost Tracking

AgentHelm includes built-in cost tracking for LLM usage:

```python
from agenthelm import CostTracker, get_cost_tracker

# Token-only tracking (no pricing)
tracker = get_cost_tracker(tokens_only=True)

# Full cost tracking with pricing
tracker = get_cost_tracker()  # Uses built-in pricing.yaml

# Track usage
tracker.record("gpt-4o", input_tokens=500, output_tokens=150)

# Get summary
summary = tracker.get_summary()
# {
#     "total_input_tokens": 500,
#     "total_output_tokens": 150,
#     "total_cost_usd": 0.0055,
#     "by_model": {...}
# }
```

## Approval Handlers

Control human-in-the-loop behavior with different handlers:

```python
from agenthelm import CliHandler, AutoApproveHandler, AutoDenyHandler

# Interactive CLI approval
tracer = ExecutionTracer(approval_handler=CliHandler())

# Auto-approve all (for testing)
tracer = ExecutionTracer(approval_handler=AutoApproveHandler())

# Auto-deny all (for dry-run)
tracer = ExecutionTracer(approval_handler=AutoDenyHandler())
```

## Storage Backends

Events can be stored in different backends:

```python
from agenthelm.core.storage import JsonStorage, SqliteStorage

# JSON file (simple, portable)
storage = JsonStorage("traces.json")

# SQLite (queryable, indexed)
storage = SqliteStorage("traces.db")

# Query by session
events = storage.query(session_id="abc-123", limit=100)
```

## Reliability Features

### Retries

```python
@tool(max_retries=3, retry_delay=1.0)
def flaky_api_call(endpoint: str) -> dict:
    """Call an external API that might fail."""
    return requests.get(endpoint).json()
```

### Human Approval

```python
@tool(requires_approval=True)
def delete_file(path: str) -> bool:
    """Delete a file (requires human approval)."""
    os.remove(path)
    return True
```

### Compensating Actions

```python
@tool(compensating_tool="restore_file")
def archive_file(path: str) -> str:
    """Archive a file (can be rolled back)."""
    archive_path = f"{path}.archived"
    shutil.move(path, archive_path)
    return archive_path

@tool()
def restore_file(archive_path: str) -> str:
    """Restore an archived file."""
    original_path = archive_path.replace(".archived", "")
    shutil.move(archive_path, original_path)
    return original_path
```