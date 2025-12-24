"""AgentHelm CLI - Command-line interface for agent orchestration."""

import click
import yaml
import json
import logging
from rich.console import Console
from rich.table import Table
from agenthelm.cli.config import (
    load_config,
    save_config,
    init_config,
    CONFIG_FILE,
    load_tools_from_string,
)


console = Console()


@click.group()
@click.version_option(version="0.3.0", prog_name="agenthelm")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose debug logging")
def cli(verbose):
    """AgentHelm - DSPy-native multi-agent orchestration."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
        logging.debug("Verbose logging enabled")
    else:
        logging.basicConfig(level=logging.WARNING)


@cli.command()
@click.argument("task")
@click.option("--model", "-m", default=None, help="LLM model to use")
@click.option("--max-iters", default=None, type=int, help="Max ReAct iterations")
@click.option("--tools", "-t", default=None, help="Tools to load (module:func,func2)")
@click.option("--trace", is_flag=True, help="Enable OpenTelemetry tracing (Jaeger)")
@click.option("--trace-endpoint", default="http://localhost:4317", help="OTLP endpoint")
@click.option(
    "--trace-storage",
    "-s",
    default=None,
    help="Path to trace storage (default: ~/.agenthelm/traces.db)",
)
def run(
    task: str,
    model: str | None,
    max_iters: int | None,
    tools: str | None,
    trace: bool,
    trace_endpoint: str,
    trace_storage: str | None,
):
    """Run a task with a ToolAgent."""
    import dspy
    from pathlib import Path
    from agenthelm import ToolAgent, ExecutionTracer
    from agenthelm.core.storage import SqliteStorage, JsonStorage
    from agenthelm.tracing import init_tracing, trace_agent as trace_agent_ctx
    from agenthelm.cli.config import CONFIG_DIR

    # Initialize OpenTelemetry tracing if enabled
    if trace:
        init_tracing(
            service_name="agenthelm-cli", otlp_endpoint=trace_endpoint, enabled=True
        )
        console.print(f"[dim]OTel tracing enabled → {trace_endpoint}[/]")

    # Load config defaults
    cfg = load_config()
    model = model or cfg.get("default_model", "mistral/mistral-large-latest")
    max_iters = max_iters or cfg.get("max_iters", 10)

    # Load tools
    tool_list = []
    if tools:
        try:
            tool_list = load_tools_from_string(tools)
            console.print(f"[dim]Loaded {len(tool_list)} tools[/]")
        except ValueError as e:
            console.print(f"[red]Error loading tools:[/] {e}")
            return

    # Setup trace storage - priority: CLI flag > config > default
    storage_path = (
        trace_storage or cfg.get("trace_storage") or str(CONFIG_DIR / "traces.db")
    )
    storage_path = Path(storage_path)
    storage_path.parent.mkdir(parents=True, exist_ok=True)

    # Auto-detect storage type
    if str(storage_path).endswith(".json"):
        db = JsonStorage(str(storage_path))
    else:
        db = SqliteStorage(str(storage_path))
    tracer = ExecutionTracer(storage=db)

    console.print(f"[bold blue]Running task:[/] {task}")
    console.print(f"[dim]Model: {model}, Max iterations: {max_iters}[/]")
    console.print(f"[dim]Traces: {storage_path}[/]")

    lm = dspy.LM(model)
    agent = ToolAgent(
        name="cli_agent",
        lm=lm,
        tools=tool_list,
        max_iters=max_iters,
        tracer=tracer,
    )

    with console.status("[bold green]Thinking..."):
        if trace:
            with trace_agent_ctx(agent_name="cli_agent", task=task):
                result = agent.run(task)
        else:
            result = agent.run(task)

    if result.success:
        console.print("\n[bold green]✓ Success[/]")
        console.print(result.answer)
    else:
        console.print("\n[bold red]✗ Failed[/]")
        console.print(result.error)

    # Show cost summary
    console.print("\n[dim]─── Summary ───[/]")
    if result.token_usage:
        total_tokens = (
            result.token_usage.input_tokens + result.token_usage.output_tokens
        )
        console.print(
            f"[dim]Tokens: {total_tokens:,} ({result.token_usage.input_tokens:,} in / {result.token_usage.output_tokens:,} out)[/]"
        )
    if result.total_cost_usd > 0:
        console.print(f"[dim]Cost: ${result.total_cost_usd:.4f}[/]")
    if result.events:
        console.print(f"[dim]Traces: {len(result.events)} events saved[/]")


@cli.command()
@click.argument("task")
@click.option("--model", "-m", default=None, help="LLM model to use")
@click.option("--approve", is_flag=True, help="Auto-approve and execute plan")
@click.option("--output", "-o", default=None, help="Save plan to YAML file")
def plan(task: str, model: str | None, approve: bool, output: str | None):
    """Generate an execution plan for a task."""
    import dspy
    from pathlib import Path
    from agenthelm import PlannerAgent

    # Load config defaults
    cfg = load_config()
    model = model or cfg.get("default_model", "mistral/mistral-large-latest")

    console.print(f"[bold blue]Planning:[/] {task}")

    lm = dspy.LM(model)
    planner = PlannerAgent(name="cli_planner", lm=lm, tools=[])

    with console.status("[bold green]Generating plan..."):
        plan_obj = planner.plan(task)

    # Display plan
    console.print(f"\n[bold]Goal:[/] {plan_obj.goal}")
    console.print(f"[dim]Reasoning: {plan_obj.reasoning}[/]\n")

    table = Table(title="Execution Plan")
    table.add_column("Step", style="cyan")
    table.add_column("Tool", style="green")
    table.add_column("Description")
    table.add_column("Depends On", style="dim")

    for step in plan_obj.steps:
        table.add_row(
            step.id, step.tool_name, step.description, ", ".join(step.depends_on) or "-"
        )

    console.print(table)

    # Save plan to file if requested
    if output:
        output_path = Path(output)
        output_path.write_text(plan_obj.to_yaml())
        console.print(f"\n[green]✓ Plan saved to {output}[/]")

    if approve:
        console.print("\n[yellow]Auto-execute not implemented yet[/]")


@cli.command()
@click.argument("plan_file", type=click.Path(exists=True))
@click.option("--model", "-m", default=None, help="LLM model to use")
@click.option("--dry-run", is_flag=True, help="Show plan without executing")
def execute(plan_file: str, model: str | None, dry_run: bool):
    """Execute a plan from a YAML file."""
    import dspy
    from pathlib import Path
    from agenthelm import Plan, ToolAgent, AgentRegistry, Orchestrator

    cfg = load_config()
    model = model or cfg.get("default_model", "mistral/mistral-large-latest")

    # Load plan from YAML
    plan_path = Path(plan_file)
    try:
        plan = Plan.from_yaml(plan_path.read_text())
    except Exception as e:
        console.print(f"[red]Error loading plan:[/] {e}")
        return

    console.print(f"[bold blue]Plan:[/] {plan.goal}")
    console.print(f"[dim]{len(plan.steps)} steps[/]\n")

    # Show steps
    table = Table(title="Execution Plan")
    table.add_column("Step", style="cyan")
    table.add_column("Tool", style="green")
    table.add_column("Description")

    for step in plan.steps:
        table.add_row(step.id, step.tool_name, step.description)

    console.print(table)

    if dry_run:
        console.print("\n[yellow]Dry run - not executing[/]")
        return

    # Confirm execution
    if not click.confirm("\nExecute this plan?"):
        console.print("[dim]Cancelled[/]")
        return

    # Create orchestrator and execute
    lm = dspy.LM(model)
    registry = AgentRegistry()

    # Register a default agent for tools
    agent = ToolAgent(name="executor", lm=lm, tools=[])
    registry.register("default", agent)

    orchestrator = Orchestrator(registry=registry)

    with console.status("[bold green]Executing plan..."):
        result_plan = orchestrator.execute(plan)

    # Show results
    success_count = sum(1 for s in result_plan.steps if s.status.value == "completed")
    console.print(
        f"\n[bold]Results:[/] {success_count}/{len(result_plan.steps)} steps completed"
    )

    for step in result_plan.steps:
        status_icon = "✓" if step.status.value == "completed" else "✗"
        color = "green" if step.status.value == "completed" else "red"
        console.print(f"  [{color}]{status_icon}[/] {step.id}: {step.status.value}")


@cli.group()
def traces():
    """View execution traces."""
    pass


@traces.command("list")
@click.option("--limit", "-n", default=10, help="Number of traces to show")
@click.option("--storage", "-s", default=None, help="Storage path (json or sqlite)")
def traces_list(limit: int, storage: str | None):
    """List recent execution traces."""
    from pathlib import Path
    from agenthelm.core.storage import SqliteStorage, JsonStorage
    from agenthelm.cli.config import load_config, CONFIG_DIR

    cfg = load_config()
    storage_path = storage or cfg.get("trace_storage") or str(CONFIG_DIR / "traces.db")

    # Auto-detect storage type
    path = Path(storage_path.replace("sqlite:///", "").replace("json:///", ""))

    if not path.exists():
        console.print(f"[yellow]No traces found at {path}[/]")
        console.print("[dim]Run a task with tracing enabled to create traces.[/]")
        return

    try:
        # Choose storage backend
        if str(path).endswith(".json"):
            db = JsonStorage(str(path))
        else:
            db = SqliteStorage(str(path))

        events = db.load()

        # Get most recent N events
        events = sorted(events, key=lambda e: e.get("timestamp", ""), reverse=True)[
            :limit
        ]

        if not events:
            console.print("[yellow]No traces found[/]")
            return

        table = Table(title="Recent Traces")
        table.add_column("Tool", style="cyan")
        table.add_column("Time", style="green")
        table.add_column("Duration")
        table.add_column("Status")

        for event in events:
            status = "[red]Failed[/]" if event.get("error_state") else "[green]OK[/]"
            table.add_row(
                event.get("tool_name", "-"),
                str(event.get("timestamp", "-"))[:19],
                f"{event.get('execution_time', 0):.3f}s",
                status,
            )

        console.print(table)
        console.print(f"\n[dim]Showing {len(events)} traces[/]")

    except Exception as e:
        console.print(f"[red]Error reading traces:[/] {e}")


@traces.command("show")
@click.argument("index", type=int)
@click.option("--storage", "-s", default=None, help="Storage path")
def traces_show(index: int, storage: str | None):
    """Show details of a trace by index (from list)."""
    from pathlib import Path
    from agenthelm.core.storage import SqliteStorage, JsonStorage
    from agenthelm.cli.config import load_config, CONFIG_DIR

    cfg = load_config()
    storage_path = storage or cfg.get("trace_storage") or str(CONFIG_DIR / "traces.db")
    path = Path(storage_path.replace("sqlite:///", "").replace("json:///", ""))

    if not path.exists():
        console.print(f"[yellow]No traces found at {path}[/]")
        return

    try:
        if str(path).endswith(".json"):
            db = JsonStorage(str(path))
        else:
            db = SqliteStorage(str(path))

        events = db.load()
        events = sorted(events, key=lambda e: e.get("timestamp", ""), reverse=True)

        if index >= len(events) or index < 0:
            console.print(
                f"[yellow]Trace index {index} not found (0-{len(events) - 1})[/]"
            )
            return

        event = events[index]

        console.print(f"\n[bold]Trace #{index}[/]")
        console.print(f"[cyan]Tool:[/] {event.get('tool_name')}")
        console.print(f"[cyan]Time:[/] {event.get('timestamp')}")
        console.print(f"[cyan]Duration:[/] {event.get('execution_time', 0):.3f}s")
        console.print(
            f"[cyan]Status:[/] {'[red]Failed[/]' if event.get('error_state') else '[green]Success[/]'}"
        )

        if event.get("inputs"):
            console.print("\n[bold]Inputs:[/]")
            console.print(json.dumps(event["inputs"], indent=2))

        if event.get("outputs"):
            console.print("\n[bold]Outputs:[/]")
            console.print(json.dumps(event["outputs"], indent=2))

        if event.get("error_state"):
            console.print(f"\n[bold red]Error:[/] {event['error_state']}")

    except Exception as e:
        console.print(f"[red]Error reading trace:[/] {e}")


@traces.command("filter")
@click.option("--tool", "-t", default=None, help="Filter by tool name")
@click.option(
    "--status",
    default=None,
    type=click.Choice(["success", "failed"]),
    help="Filter by status",
)
@click.option("--date-from", default=None, help="Filter from date (YYYY-MM-DD)")
@click.option("--date-to", default=None, help="Filter to date (YYYY-MM-DD)")
@click.option(
    "--min-time", default=None, type=float, help="Min execution time (seconds)"
)
@click.option(
    "--max-time", default=None, type=float, help="Max execution time (seconds)"
)
@click.option("--limit", "-n", default=50, help="Max results")
@click.option("--storage", "-s", default=None, help="Storage path")
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON")
def traces_filter(
    tool, status, date_from, date_to, min_time, max_time, limit, storage, json_output
):
    """Filter traces by various criteria."""
    from pathlib import Path
    from agenthelm.core.storage import SqliteStorage, JsonStorage
    from agenthelm.cli.config import load_config, CONFIG_DIR

    cfg = load_config()
    storage_path = storage or cfg.get("trace_storage") or str(CONFIG_DIR / "traces.db")
    path = Path(storage_path.replace("sqlite:///", "").replace("json:///", ""))

    if not path.exists():
        console.print(f"[yellow]No traces found at {path}[/]")
        return

    try:
        db = (
            JsonStorage(str(path))
            if str(path).endswith(".json")
            else SqliteStorage(str(path))
        )
        events = db.load()

        # Apply filters
        filtered = []
        for e in events:
            if tool and e.get("tool_name") != tool:
                continue
            if status == "success" and e.get("error_state"):
                continue
            if status == "failed" and not e.get("error_state"):
                continue
            if date_from:
                ts = e.get("timestamp", "")[:10]
                if ts < date_from:
                    continue
            if date_to:
                ts = e.get("timestamp", "")[:10]
                if ts > date_to:
                    continue
            if min_time and e.get("execution_time", 0) < min_time:
                continue
            if max_time and e.get("execution_time", float("inf")) > max_time:
                continue
            filtered.append(e)

        filtered = sorted(filtered, key=lambda x: x.get("timestamp", ""), reverse=True)[
            :limit
        ]

        if json_output:
            console.print(json.dumps(filtered, indent=2, default=str))
            return

        if not filtered:
            console.print("[yellow]No traces match criteria[/]")
            return

        table = Table(title=f"Filtered Traces ({len(filtered)} results)")
        table.add_column("ID", style="dim")
        table.add_column("Tool", style="cyan")
        table.add_column("Time", style="green")
        table.add_column("Duration")
        table.add_column("Status")

        for i, e in enumerate(filtered):
            status_str = "[red]FAILED[/]" if e.get("error_state") else "[green]OK[/]"
            table.add_row(
                str(i),
                e.get("tool_name", "-"),
                str(e.get("timestamp", "-"))[:19],
                f"{e.get('execution_time', 0):.3f}s",
                status_str,
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/] {e}")


@traces.command("export")
@click.option("--output", "-o", required=True, help="Output file path")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "csv", "md"]),
    default="json",
    help="Export format",
)
@click.option("--tool", "-t", default=None, help="Filter by tool name")
@click.option(
    "--status",
    default=None,
    type=click.Choice(["success", "failed"]),
    help="Filter by status",
)
@click.option("--storage", "-s", default=None, help="Storage path")
def traces_export(output, format, tool, status, storage):
    """Export traces to JSON, CSV, or Markdown."""
    import csv
    from pathlib import Path
    from datetime import datetime
    from agenthelm.core.storage import SqliteStorage, JsonStorage
    from agenthelm.cli.config import load_config, CONFIG_DIR

    cfg = load_config()
    storage_path = storage or cfg.get("trace_storage") or str(CONFIG_DIR / "traces.db")
    path = Path(storage_path.replace("sqlite:///", "").replace("json:///", ""))

    if not path.exists():
        console.print(f"[yellow]No traces found at {path}[/]")
        return

    try:
        db = (
            JsonStorage(str(path))
            if str(path).endswith(".json")
            else SqliteStorage(str(path))
        )
        events = db.load()

        # Apply filters
        filtered = []
        for e in events:
            if tool and e.get("tool_name") != tool:
                continue
            if status == "success" and e.get("error_state"):
                continue
            if status == "failed" and not e.get("error_state"):
                continue
            filtered.append(e)

        if not filtered:
            console.print("[yellow]No traces to export[/]")
            return

        if format == "json":
            with open(output, "w") as f:
                json.dump(filtered, f, indent=2, default=str)

        elif format == "csv":
            keys = ["timestamp", "tool_name", "execution_time", "error_state"]
            with open(output, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(filtered)

        elif format == "md":
            with open(output, "w") as f:
                f.write("# AgentHelm Trace Export\n\n")
                f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for i, e in enumerate(filtered):
                    f.write(f"## Trace {i}\n")
                    f.write(f"- **Tool**: {e.get('tool_name')}\n")
                    f.write(f"- **Time**: {e.get('timestamp')}\n")
                    f.write(f"- **Duration**: {e.get('execution_time', 0):.3f}s\n")
                    f.write(
                        f"- **Status**: {'FAILED' if e.get('error_state') else 'SUCCESS'}\n\n"
                    )

        console.print(f"[green]✓ Exported {len(filtered)} traces to {output}[/]")

    except Exception as e:
        console.print(f"[red]Error:[/] {e}")


@cli.command()
def init():
    """Initialize AgentHelm configuration."""
    config_path = init_config()
    console.print(f"[green]✓ Config initialized at:[/] {config_path}")
    console.print(
        "\n[dim]Edit this file or use 'agenthelm config set' to configure.[/]"
    )


@cli.group()
def config():
    """Manage configuration."""
    pass


@config.command("show")
def config_show():
    """Show current configuration."""
    cfg = load_config()

    # Mask API keys
    if cfg.get("api_keys"):
        for provider, key in cfg["api_keys"].items():
            if key:
                cfg["api_keys"][provider] = key[:8] + "..." + key[-4:]

    console.print(yaml.dump(cfg, default_flow_style=False))


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """Set a configuration value (e.g., 'agenthelm config set default_model gpt-4')."""
    cfg = load_config()

    # Handle nested keys like "api_keys.openai"
    parts = key.split(".")
    target = cfg
    for part in parts[:-1]:
        if part not in target:
            target[part] = {}
        target = target[part]
    target[parts[-1]] = value

    save_config(cfg)
    console.print(f"[green]✓ Set {key} = {value}[/]")


@config.command("path")
def config_path():
    """Show config file path."""
    console.print(f"{CONFIG_FILE}")


@cli.group()
def mcp():
    """Manage MCP server connections."""
    pass


@mcp.command("list-tools")
@click.argument("command")
@click.argument("args", nargs=-1)
def mcp_list_tools(command: str, args: tuple):
    """
    List tools from an MCP server.

    Example: agenthelm mcp list-tools uvx mcp-server-time
    """
    import asyncio
    from agenthelm import MCPClient

    async def list_tools():
        async with MCPClient({"command": command, "args": list(args)}) as client:
            with console.status(f"[bold green]Connecting to {command}..."):
                pass  # Connection happens in __aenter__
            tools = await client.list_tools()
            return tools

    try:
        tools = asyncio.run(list_tools())

        table = Table(title=f"Tools from {command}")
        table.add_column("Name", style="cyan")
        table.add_column("Description")

        for tool in tools:
            table.add_row(tool["name"], tool.get("description", "-")[:60])

        console.print(table)
        console.print(f"\n[dim]Total: {len(tools)} tools[/]")

    except FileNotFoundError:
        console.print(f"[red]Error:[/] Command not found: {command}")
        console.print("[dim]Make sure the MCP server is installed.[/]")
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")


@mcp.command("run")
@click.argument("command")
@click.argument("server_args", nargs=-1)
@click.option("--task", "-t", required=True, help="Task to execute")
@click.option("--model", "-m", default=None, help="LLM model")
def mcp_run(command: str, server_args: tuple, task: str, model: str | None):
    """
    Run a task using tools from an MCP server.

    Example: agenthelm mcp run uvx mcp-server-time -t "What time is it?"
    """
    import asyncio
    import dspy
    from agenthelm import MCPToolAdapter, ToolAgent
    from agenthelm.cli.config import load_config

    cfg = load_config()
    model = model or cfg.get("default_model", "mistral/mistral-large-latest")

    async def run_with_mcp():
        adapter = MCPToolAdapter({"command": command, "args": list(server_args)})

        with console.status(f"[bold green]Connecting to {command}..."):
            await adapter.connect()

        tools = adapter.get_tools()
        console.print(f"[dim]Loaded {len(tools)} tools from MCP server[/]")

        lm = dspy.LM(model)
        agent = ToolAgent(name="mcp_agent", lm=lm, tools=tools)

        with console.status("[bold green]Thinking..."):
            result = agent.run(task)

        await adapter.close()
        return result

    try:
        result = asyncio.run(run_with_mcp())

        if result.success:
            console.print("\n[bold green]✓ Success[/]")
            console.print(result.answer)
        else:
            console.print("\n[bold red]✗ Failed[/]")
            console.print(result.error)

    except Exception as e:
        console.print(f"[red]Error:[/] {e}")


@cli.command()
@click.option("--model", "-m", default=None, help="LLM model to use")
@click.option("--tools", "-t", default=None, help="Tools to load (module:func,func2)")
def chat(model: str | None, tools: str | None):
    """Interactive chat mode (REPL)."""
    import dspy
    from agenthelm import ToolAgent

    cfg = load_config()
    model = model or cfg.get("default_model", "openai/gpt-4o-mini")

    # Load tools
    tool_list = []
    if tools:
        try:
            tool_list = load_tools_from_string(tools)
            console.print(f"[dim]Loaded {len(tool_list)} tools[/]")
        except ValueError as e:
            console.print(f"[red]Error loading tools:[/] {e}")
            return

    console.print(f"[bold blue]AgentHelm Chat[/] (model: {model})")
    console.print("[dim]Type 'exit' or 'quit' to end the session[/]\n")

    lm = dspy.LM(model)
    agent = ToolAgent(name="chat_agent", lm=lm, tools=tool_list)

    while True:
        try:
            task = console.input("[bold green]> [/]")

            if task.lower() in ("exit", "quit", "q"):
                console.print("[dim]Goodbye![/]")
                break

            if not task.strip():
                continue

            with console.status("[bold green]Thinking..."):
                result = agent.run(task)

            if result.success:
                console.print(f"\n[cyan]{result.answer}[/]\n")
            else:
                console.print(f"\n[red]Error: {result.error}[/]\n")

        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Type 'exit' to quit.[/]")
        except EOFError:
            break


if __name__ == "__main__":
    cli()
