# Command Line Interface

AgentHelm provides a powerful CLI for running agents, managing plans, and viewing traces.

## Installation

```bash
pip install agenthelm
```

## Quick Start

```bash
# Initialize configuration
agenthelm init

# Run a simple task
agenthelm run "What is 2+2?"

# Interactive chat mode
agenthelm chat
```

## Commands

### `agenthelm run`

Run a task with a ToolAgent.

```bash
agenthelm run "Search for AI news and summarize" \
  --model mistral/mistral-large-latest \
  --tools mytools:search,summarize \
  --trace
```

| Option                | Description                            |
|-----------------------|----------------------------------------|
| `-m, --model`         | LLM model (default: from config)       |
| `-t, --tools`         | Tools to load (`module:func,func2`)    |
| `--max-iters`         | Max reasoning iterations (default: 10) |
| `--trace`             | Enable OpenTelemetry/Jaeger tracing    |
| `-s, --trace-storage` | Custom trace storage path              |

---

### `agenthelm plan`

Generate an execution plan for a complex task.

```bash
# Generate and display a plan
agenthelm plan "Build a web scraper for news sites"

# Save plan to file
agenthelm plan "Build a web scraper" -o plan.yaml
```

| Option         | Description                |
|----------------|----------------------------|
| `-m, --model`  | LLM model                  |
| `-o, --output` | Save plan to YAML file     |
| `--approve`    | Auto-approve for execution |

---

### `agenthelm execute`

Execute a plan from a YAML file.

```bash
# Preview plan
agenthelm execute plan.yaml --dry-run

# Execute with confirmation
agenthelm execute plan.yaml
```

| Option        | Description               |
|---------------|---------------------------|
| `-m, --model` | LLM model                 |
| `--dry-run`   | Preview without executing |

---

### `agenthelm chat`

Interactive REPL mode for conversational tasks.

```bash
agenthelm chat --model mistral/mistral-large-latest
```

```
AgentHelm Chat (model: mistral/mistral-large-latest)
Type 'exit' or 'quit' to end the session

> What is the capital of France?
Paris is the capital of France.

> exit
Goodbye!
```

---

### `agenthelm traces`

View and manage execution traces.

#### List traces

```bash
agenthelm traces list
agenthelm traces list -n 20
```

#### Show trace details

```bash
agenthelm traces show 0     # Show most recent trace
```

#### Filter traces

```bash
# By tool name
agenthelm traces filter --tool search

# By status
agenthelm traces filter --status success

# By date range
agenthelm traces filter --date-from 2024-01-01 --date-to 2024-12-31

# Output as JSON
agenthelm traces filter --status failed --json
```

#### Export traces

```bash
# Export to JSON
agenthelm traces export -o report.json -f json

# Export to CSV
agenthelm traces export -o report.csv -f csv

# Export to Markdown
agenthelm traces export -o report.md -f md
```

---

### `agenthelm mcp`

Manage MCP (Model Context Protocol) server connections.

#### List MCP tools

```bash
agenthelm mcp list-tools uvx mcp-server-time
```

#### Run task with MCP tools

```bash
agenthelm mcp run uvx mcp-server-time -t "What time is it?"
```

---

### `agenthelm config`

Manage configuration settings.

```bash
# Show current config
agenthelm config show

# Set default model
agenthelm config set default_model mistral/mistral-large-latest

# Set API key
agenthelm config set api_keys.openai sk-...

# Show config file path
agenthelm config path
```

---

### `agenthelm init`

Initialize AgentHelm configuration.

```bash
agenthelm init
```

Creates `~/.agenthelm/config.yaml` with default settings.

---

## Global Options

| Option          | Description          |
|-----------------|----------------------|
| `-v, --verbose` | Enable debug logging |
| `--version`     | Show version         |
| `--help`        | Show help            |

## Configuration

Configuration is stored in `~/.agenthelm/config.yaml`:

```yaml
default_model: mistral/mistral-large-latest
max_iters: 10
trace_storage: ~/.agenthelm/traces.db
api_keys:
  openai: sk-...
  anthropic: sk-...
```

### Environment Variables

| Variable            | Description            |
|---------------------|------------------------|
| `OPENAI_API_KEY`    | OpenAI API key         |
| `ANTHROPIC_API_KEY` | Anthropic API key      |
| `MISTRAL_API_KEY`   | Mistral API key        |
| `AGENTHELM_MODEL`   | Override default model |

## Trace Storage

Traces are automatically saved to `~/.agenthelm/traces.db`.

Override with:

- CLI flag: `--trace-storage /path/to/traces.db`
- Config: `trace_storage: /path/to/traces.db`

Supported formats:

- SQLite (`.db`, `.sqlite`)
- JSON (`.json`)
