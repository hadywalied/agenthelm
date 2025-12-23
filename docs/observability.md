# Observability & Trace Explorer

AgentHelm v0.2.0 introduces a robust observability system and a powerful CLI-based trace explorer, allowing you to gain
deep insights into your agent's execution, debug issues, and ensure reliability.

## Standardized Logging

All internal `print()` statements have been replaced with Python's standard `logging` module. This provides granular
control over the verbosity of output.

- `logging.info()`: Used for high-level, user-facing messages, indicating major steps in the agent's execution.
- `logging.debug()`: Provides detailed information, such as LLM responses, tool arguments, and internal processing
  steps. Useful for in-depth debugging.
- `logging.warning()`: Indicates non-critical issues or potential problems.
- `logging.error()`: Signals critical errors that prevent the agent from completing its task.

### Controlling Logging Verbosity

Use the `-v` or `--verbose` flag when running your agent to enable `DEBUG`-level logging:

```bash
agenthelm run \
  --agent-file examples/cli_tools_example/my_agent_tools.py \
  --task "What is the weather in New York?" \
  --verbose
```

By default, only `INFO` level messages and above are displayed.

## Storage Abstraction Layer

AgentHelm now features a flexible storage abstraction layer, allowing you to choose how your agent's execution traces
are persisted. This enables better integration with different environments and provides options for performance and
querying capabilities.

### Available Storage Backends

- **JSON Storage (`.json`)**: This is the default storage backend. Traces are saved as a list of JSON objects in a
  single file. It's simple, human-readable, and excellent for local development and smaller trace volumes.

  ```python
  from agenthelm.core.storage import JsonStorage
  storage = JsonStorage("my_agent_traces.json")
  ```

- **SQLite Storage (`.db`)**: A lightweight, file-based relational database. SQLite offers significantly better
  performance for querying and filtering large numbers of traces compared to JSON files. It's recommended for more
  extensive trace logging and when you need to perform complex queries.

  ```python
  from agenthelm.core.storage import SqliteStorage
  storage = SqliteStorage("my_agent_traces.db")
  ```

### Specifying Storage

You can specify the storage file and type using the `--trace-file` option in the `agenthelm run` command. The backend is
automatically determined by the file extension (`.json` for JSON, `.db` for SQLite).

```bash
# Using JSON storage (default)
agenthelm run --agent-file tools.py --task "..." --trace-file cli_trace.json

# Using SQLite storage
agenthelm run --agent-file tools.py --task "..." --trace-file my_traces.db
```

## CLI Trace Explorer

The `agenthelm traces` command provides a powerful interface to inspect, filter, and export your agent's execution
traces directly from the command line.

### `agenthelm traces list`

Lists recent agent execution traces in a table format. Supports pagination.

```bash
# List the 10 most recent traces from the default JSON file
agenthelm traces list

# List 5 traces starting from the 3rd trace (offset 2) from a SQLite database
agenthelm traces list --limit 5 --offset 2 --trace-file my_traces.db

# Output traces in raw JSON format
agenthelm traces list --json
```

### `agenthelm traces show <ID>`

Displays detailed information for a specific trace, including inputs, outputs, LLM reasoning, and confidence scores.

```bash
# Show details for trace with ID 0 from the default JSON file
agenthelm traces show 0

# Show details for trace with ID 5 from a SQLite database
agenthelm traces show 5 --trace-file my_traces.db
```

### `agenthelm traces filter`

Filters traces based on various criteria and displays the results in a table.

```bash
# Filter traces by tool name and status
agenthelm traces filter --tool-name get_weather --status success

# Filter traces that failed within a specific date range
agenthelm traces filter --status failed --date-from 2025-10-01 --date-to 2025-10-31 --trace-file my_traces.db

# Filter traces with high execution time and low confidence, output as JSON
agenthelm traces filter --min-time 5.0 --confidence-max 0.7 --json
```

### `agenthelm traces export`

Exports filtered traces to different file formats (CSV, JSON, Markdown).

```bash
# Export all failed traces to a CSV file
agenthelm traces export --output failed_traces.csv --format csv --status failed

# Export all traces to a JSON file
agenthelm traces export --output all_traces.json --format json --trace-file my_traces.db

# Export traces from a specific tool to a Markdown report
agenthelm traces export --output weather_tool_report.md --format md --tool-name get_weather
```
