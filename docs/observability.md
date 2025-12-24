# Observability & Tracing

AgentHelm provides comprehensive observability through execution tracing, cost tracking, and OpenTelemetry integration.

## Execution Tracing

Every tool execution is automatically traced and stored:

```python
from agenthelm import ExecutionTracer, ToolAgent
from agenthelm.core.storage import SqliteStorage

# Create tracer with storage
storage = SqliteStorage("traces.db")
tracer = ExecutionTracer(storage=storage)

# Pass to agent
agent = ToolAgent(
    name="my_agent",
    lm=lm,
    tools=[my_tool],
    tracer=tracer,  # Traces saved automatically
)
```

### Event Model

Each execution produces an `Event` with:

| Field                | Description                |
|----------------------|----------------------------|
| `timestamp`          | When the event occurred    |
| `tool_name`          | Name of the executed tool  |
| `inputs` / `outputs` | Arguments and return value |
| `execution_time`     | Duration in seconds        |
| `token_usage`        | LLM tokens (input/output)  |
| `estimated_cost_usd` | Cost estimate              |
| `agent_name`         | Which agent executed this  |
| `trace_id`           | Unique execution ID        |

## CLI Trace Explorer

### List Traces

```bash
# List recent traces
agenthelm traces list

# Limit results
agenthelm traces list -n 20
```

### Show Trace Details

```bash
agenthelm traces show 0
```

### Filter Traces

```bash
# By tool name
agenthelm traces filter --tool get_weather

# By status
agenthelm traces filter --status success
agenthelm traces filter --status failed

# By date range
agenthelm traces filter --date-from 2024-01-01 --date-to 2024-12-31

# By execution time
agenthelm traces filter --min-time 1.0 --max-time 5.0

# Output as JSON
agenthelm traces filter --status failed --json
```

### Export Traces

```bash
# Export to JSON
agenthelm traces export -o traces.json -f json

# Export to CSV
agenthelm traces export -o traces.csv -f csv

# Export to Markdown report
agenthelm traces export -o report.md -f md

# Export filtered traces
agenthelm traces export -o failed.md -f md --status failed
```

## Storage Backends

### SQLite (Default)

```bash
# Traces saved to ~/.agenthelm/traces.db by default
agenthelm run "task"

# Custom path
agenthelm run "task" -s ./my_traces.db
```

### JSON

```bash
agenthelm run "task" -s ./traces.json
```

### Configure Default Storage

```bash
agenthelm config set trace_storage /path/to/traces.db
```

## OpenTelemetry & Jaeger

AgentHelm supports OpenTelemetry for distributed tracing with Jaeger.

### Setup Jaeger

```bash
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 4317:4317 \
  jaegertracing/all-in-one:latest
```

### Enable Tracing

```bash
# Run with OpenTelemetry tracing
agenthelm run "What is 2+2?" --trace

# Custom endpoint
agenthelm run "task" --trace --trace-endpoint http://localhost:4317
```

### View in Jaeger UI

Open http://localhost:16686 and select "agenthelm-cli" service.

### Python SDK

```python
from agenthelm.tracing import init_tracing, trace_tool, trace_agent

# Initialize OpenTelemetry
init_tracing(
    service_name="my-app",
    otlp_endpoint="http://localhost:4317",
    enabled=True,
)

# Trace a tool execution
with trace_tool("search", inputs={"query": "AI news"}) as span:
    result = search("AI news")
    span.set_attribute("result_count", len(result))

# Trace an agent execution
with trace_agent("researcher", task="Find AI news") as span:
    result = agent.run("Find AI news")
```

## Verbose Logging

Enable debug logging with the `-v` flag:

```bash
agenthelm -v run "task"
agenthelm -v traces list
```

## Cost Tracking

Track token usage and estimated costs:

```python
from agenthelm import CostTracker, get_cost_tracker

# Get tracker
tracker = get_cost_tracker()

# Record usage
tracker.record("mistral-large-latest", input_tokens=500, output_tokens=150)

# Get summary
summary = tracker.get_summary()
print(f"Total cost: ${summary['total_cost_usd']:.4f}")
```

The CLI shows cost summary after each run:

```
─── Summary ───
Tokens: 1,234 (856 in / 378 out)
Cost: $0.0042
Traces: 3 events saved
```
