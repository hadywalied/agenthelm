"""Command-line interface for AgentHelm."""

from enum import Enum
import typer
import os
import importlib.util
import inspect
import logging
import json
from typing import List, Callable, Optional
from datetime import datetime
from tabulate import tabulate
import csv
import sys

from orchestrator.core.storage.json_storage import JsonStorage
from orchestrator.core.storage.sqlite_storage import SqliteStorage
from orchestrator.core.storage.base import BaseStorage
from orchestrator.core.tool import TOOL_REGISTRY
from orchestrator.core.tracer import ExecutionTracer
from orchestrator.agent import Agent
from orchestrator.llm.mistral_client import MistralClient
from orchestrator.llm.openai_client import OpenAIClient


class LLM_TYPE(str, Enum):
    MISTRAL = "mistral"
    OPENAI = "openai"


app = typer.Typer(help="A CLI for running and observing AI agents.")

traces_app = typer.Typer(help="Manage and view agent execution traces.")
app.add_typer(traces_app, name="traces")


def get_storage_from_file(trace_file: str) -> BaseStorage:
    """Helper function to get the appropriate storage backend."""
    if trace_file.endswith(".json"):
        return JsonStorage(trace_file)
    elif trace_file.endswith(".db") or trace_file.endswith(".sqlite"):
        return SqliteStorage(trace_file)
    else:
        logging.error(
            "Error: Unsupported storage file type. Use .json, .db, or .sqlite"
        )
        raise typer.Exit(code=1)


@app.callback()
def main(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose DEBUG-level logging."
    ),
):
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(message)s", stream=sys.stdout)
    if verbose:
        logging.debug("Verbose logging enabled.")


@app.command()
def help():
    """Display a custom help message for the AgentHelm CLI."""
    typer.echo("Welcome to AgentHelm - The Docker for AI Agents")
    typer.echo("Run 'agenthelm run --help' for detailed command usage.")


def load_tools_from_file(filepath: str) -> List[Callable]:
    """Dynamically loads a Python file and discovers functions decorated with @tool."""
    module_name = f"agent_tools.{os.path.basename(filepath).replace('.py', '')}"
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    if not spec or not spec.loader:
        raise ImportError(f"Could not load spec from {filepath}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    discovered_tools = [
        obj
        for name, obj in inspect.getmembers(module)
        if inspect.isfunction(obj) and name in TOOL_REGISTRY
    ]
    return discovered_tools


@app.command()
def run(
    agent_file: str = typer.Option(
        ..., help="The path to the Python file containing tool definitions."
    ),
    task: str = typer.Option(
        ..., help="The natural language task for the agent to perform."
    ),
    llm_type: LLM_TYPE = typer.Option(LLM_TYPE.MISTRAL, help="The type of LLM to use."),
    max_steps: int = typer.Option(
        10, help="The maximum number of steps to run the agent for."
    ),
    trace_file: str = typer.Option(
        "cli_trace.json", help="The path to the output trace file."
    ),
):
    """Runs the agent with a specified set of tools and a task."""
    logging.info(f"Loading tools from: {agent_file}")
    try:
        agent_tools = load_tools_from_file(agent_file)
        if not agent_tools:
            logging.error(
                f"Error: No tools found in {agent_file}. Make sure your functions are decorated with @tool."
            )
            raise typer.Exit(code=1)
        logging.info(
            f"Found {len(agent_tools)} tools: {[t.__name__ for t in agent_tools]}"
        )
    except Exception as e:
        logging.error(f"Error loading tools file: {e}")
        raise typer.Exit(code=1)

    # 1. Setup the components
    storage = get_storage_from_file(trace_file)

    tracer = ExecutionTracer(storage)

    if llm_type == LLM_TYPE.MISTRAL:
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            logging.error("Error: MISTRAL_API_KEY environment variable not set.")
            raise typer.Exit(code=1)
        model_name = os.environ.get("MISTRAL_MODEL_NAME", "mistral-small-latest")
        logging.info(f"Using MISTRAL model: {model_name}")
        client = MistralClient(model_name=model_name, api_key=api_key)
    elif llm_type == LLM_TYPE.OPENAI:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logging.error("Error: OPENAI_API_KEY environment variable not set.")
            raise typer.Exit(code=1)
        model_name = os.environ.get("OPENAI_MODEL_NAME", "gpt-4")
        logging.info(f"Using OPENAI model: {model_name}")
        client = OpenAIClient(model_name=model_name, api_key=api_key)
    else:
        logging.error(f"Unsupported LLM type: {llm_type}")
        raise typer.Exit(code=1)

    # 2. Instantiate the Agent
    agent = Agent(tools=agent_tools, tracer=tracer, client=client)

    # 3. Run the agent with the task
    logging.info(f"\nRunning agent with task: '{task}'")
    agent.run_react(task, max_steps)

    logging.info("\nAgent run finished.")


@traces_app.command("list")
def list_traces(
    limit: int = typer.Option(10, help="Limit the number of traces to display."),
    offset: int = typer.Option(0, help="Offset for pagination."),
    trace_file: str = typer.Option(
        "cli_trace.json", help="The path to the trace file (JSON or SQLite)."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output traces in JSON format."
    ),
):
    """List recent agent execution traces."""
    storage = get_storage_from_file(trace_file)

    traces = storage.load()

    if not traces:
        typer.echo("No traces found.")
        raise typer.Exit(code=0)

    # Apply pagination
    paginated_traces = traces[offset : offset + limit]

    if json_output:
        typer.echo(json.dumps(paginated_traces, indent=2, default=str))
    else:
        headers = ["ID", "Timestamp", "Tool Name", "Status", "Execution Time (s)"]
        table_data = []
        for i, trace in enumerate(paginated_traces):
            status = "SUCCESS" if trace.get("error_state") is None else "FAILED"
            timestamp = datetime.fromisoformat(trace["timestamp"]).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            table_data.append(
                [
                    i + offset,
                    timestamp,
                    trace["tool_name"],
                    status,
                    f"{trace['execution_time']:.2f}",
                ]
            )

        typer.echo(tabulate(table_data, headers=headers, tablefmt="grid"))


@traces_app.command("show")
def show_trace(
    trace_id: int = typer.Argument(..., help="The ID of the trace to display."),
    trace_file: str = typer.Option(
        "cli_trace.json", help="The path to the trace file (JSON or SQLite)."
    ),
):
    """Show detailed information for a specific agent execution trace."""
    storage = get_storage_from_file(trace_file)

    traces = storage.load()

    if not traces:
        typer.echo("No traces found.", err=True)
        raise typer.Exit(code=1)

    # Adjust trace_id for 0-based indexing if necessary
    if trace_id < 0 or trace_id >= len(traces):
        typer.echo(f"Error: Trace ID {trace_id} not found.", err=True)
        raise typer.Exit(code=1)

    trace = traces[trace_id]

    typer.echo(f"\n--- Trace Details (ID: {trace_id}) ---")
    typer.echo(
        f"Timestamp: {datetime.fromisoformat(trace['timestamp']).strftime('%Y-%m-%d %H:%M:%S %Z')}"
    )
    typer.echo(f"Tool Name: {trace['tool_name']}")
    typer.echo(f"Execution Time: {trace['execution_time']:.2f} seconds")
    typer.echo(f"Confidence Score: {trace['confidence_score']:.2f}")
    typer.echo(f"LLM Reasoning: {trace['llm_reasoning_trace']}")

    if trace.get("error_state"):
        typer.echo(f"Status: FAILED - {trace['error_state']}")
    else:
        typer.echo("Status: SUCCESS")

    typer.echo("Inputs:")
    typer.echo(json.dumps(trace.get("inputs", {}), indent=2))

    typer.echo("Outputs:")
    typer.echo(json.dumps(trace.get("outputs", {}), indent=2))


@traces_app.command("filter")
def filter_traces(
    tool_name: Optional[str] = typer.Option(None, help="Filter by tool name."),
    status: Optional[str] = typer.Option(
        None, help="Filter by status (success/failed)."
    ),
    date_from: Optional[datetime] = typer.Option(
        None, help="Filter traces from this date (YYYY-MM-DD)."
    ),
    date_to: Optional[datetime] = typer.Option(
        None, help="Filter traces up to this date (YYYY-MM-DD)."
    ),
    min_time: Optional[float] = typer.Option(
        None, help="Filter by minimum execution time in seconds."
    ),
    max_time: Optional[float] = typer.Option(
        None, help="Filter by maximum execution time in seconds."
    ),
    confidence_min: Optional[float] = typer.Option(
        None, help="Filter by minimum confidence score (0.0-1.0)."
    ),
    confidence_max: Optional[float] = typer.Option(
        None, help="Filter by maximum confidence score (0.0-1.0)."
    ),
    trace_file: str = typer.Option(
        "cli_trace.json", help="The path to the trace file (JSON or SQLite)."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output traces in JSON format."
    ),
):
    """Filter and display agent execution traces based on various criteria."""
    storage = get_storage_from_file(trace_file)

    traces = storage.load()

    if not traces:
        typer.echo("No traces found.")
        raise typer.Exit(code=0)

    filtered_traces = []
    for trace in traces:
        match = True

        # Filter by tool name
        if tool_name and trace.get("tool_name") != tool_name:
            match = False

        # Filter by status
        if status:
            trace_status = "success" if trace.get("error_state") is None else "failed"
            if status.lower() != trace_status:
                match = False

        # Filter by date range
        trace_datetime = datetime.fromisoformat(trace["timestamp"])
        if date_from and trace_datetime.date() < date_from.date():
            match = False
        if date_to and trace_datetime.date() > date_to.date():
            match = False

        # Filter by execution time range
        if min_time and trace.get("execution_time", 0) < min_time:
            match = False
        if max_time and trace.get("execution_time", float("inf")) > max_time:
            match = False

        # Filter by confidence score range
        if confidence_min and trace.get("confidence_score", 0.0) < confidence_min:
            match = False
        if confidence_max and trace.get("confidence_score", 1.0) > confidence_max:
            match = False

        if match:
            filtered_traces.append(trace)

    if not filtered_traces:
        typer.echo("No traces found matching the criteria.")
        raise typer.Exit(code=0)

    if json_output:
        typer.echo(json.dumps(filtered_traces, indent=2, default=str))
    else:
        headers = [
            "ID",
            "Timestamp",
            "Tool Name",
            "Status",
            "Execution Time (s)",
            "Confidence",
        ]
        table_data = []
        for i, trace in enumerate(filtered_traces):
            status = "SUCCESS" if trace.get("error_state") is None else "FAILED"
            timestamp = datetime.fromisoformat(trace["timestamp"]).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            table_data.append(
                [
                    i,
                    timestamp,
                    trace["tool_name"],
                    status,
                    f"{trace['execution_time']:.2f}",
                    f"{trace['confidence_score']:.2f}",
                ]
            )

        typer.echo(tabulate(table_data, headers=headers, tablefmt="grid"))


@traces_app.command("export")
def export_traces(
    output: str = typer.Option(..., help="Output file path."),
    format: str = typer.Option(..., help="Output format (csv, json, md)."),
    tool_name: Optional[str] = typer.Option(None, help="Filter by tool name."),
    status: Optional[str] = typer.Option(
        None, help="Filter by status (success/failed)."
    ),
    date_from: Optional[datetime] = typer.Option(
        None, help="Filter traces from this date (YYYY-MM-DD)."
    ),
    date_to: Optional[datetime] = typer.Option(
        None, help="Filter traces up to this date (YYYY-MM-DD)."
    ),
    min_time: Optional[float] = typer.Option(
        None, help="Filter by minimum execution time in seconds."
    ),
    max_time: Optional[float] = typer.Option(
        None, help="Filter by maximum execution time in seconds."
    ),
    confidence_min: Optional[float] = typer.Option(
        None, help="Filter by minimum confidence score (0.0-1.0)."
    ),
    confidence_max: Optional[float] = typer.Option(
        None, help="Filter by maximum confidence score (0.0-1.0)."
    ),
    trace_file: str = typer.Option(
        "cli_trace.json", help="The path to the trace file (JSON or SQLite)."
    ),
):
    """Export agent execution traces to a specified format."""
    storage = get_storage_from_file(trace_file)

    traces = storage.load()

    if not traces:
        typer.echo("No traces found.")
        raise typer.Exit(code=0)

    filtered_traces = []
    for trace in traces:
        match = True

        # Filter by tool name
        if tool_name and trace.get("tool_name") != tool_name:
            match = False

        # Filter by status
        if status:
            trace_status = "success" if trace.get("error_state") is None else "failed"
            if status.lower() != trace_status:
                match = False

        # Filter by date range
        trace_datetime = datetime.fromisoformat(trace["timestamp"])
        if date_from and trace_datetime.date() < date_from.date():
            match = False
        if date_to and trace_datetime.date() > date_to.date():
            match = False

        # Filter by execution time range
        if min_time and trace.get("execution_time", 0) < min_time:
            match = False
        if max_time and trace.get("execution_time", float("inf")) > max_time:
            match = False

        # Filter by confidence score range
        if confidence_min and trace.get("confidence_score", 0.0) < confidence_min:
            match = False
        if confidence_max and trace.get("confidence_score", 1.0) > confidence_max:
            match = False

        if match:
            filtered_traces.append(trace)

    if not filtered_traces:
        typer.echo("No traces found matching the criteria.")
        raise typer.Exit(code=0)

    if format == "json":
        with open(output, "w") as f:
            json.dump(filtered_traces, f, indent=2, default=str)
        typer.echo(f"Traces exported to {output} in JSON format.")
    elif format == "csv":
        if not filtered_traces:
            typer.echo("No traces to export.")
            return

        # Get headers from the first trace, ensuring all keys are included
        all_keys = set()
        for trace in filtered_traces:
            all_keys.update(trace.keys())
        headers = sorted(list(all_keys))

        with open(output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for trace in filtered_traces:
                # Flatten nested dicts for CSV
                row = {
                    k: (json.dumps(v) if isinstance(v, (dict, list)) else v)
                    for k, v in trace.items()
                }
                writer.writerow(row)
        typer.echo(f"Traces exported to {output} in CSV format.")
    elif format == "md":
        with open(output, "w") as f:
            f.write("# AgentHelm Trace Export\n\n")
            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Filter Criteria\n\n")
            filters_applied = {
                "tool_name": tool_name,
                "status": status,
                "date_from": date_from,
                "date_to": date_to,
                "min_time": min_time,
                "max_time": max_time,
                "confidence_min": confidence_min,
                "confidence_max": confidence_max,
            }
            for k, v in filters_applied.items():
                if v is not None:
                    f.write(f"- **{k.replace('_', ' ').title()}**: {v}\n")
            f.write("\n")

            for i, trace in enumerate(filtered_traces):
                f.write(f"---\n\n### Trace ID: {i}\n")
                f.write(
                    f"- **Timestamp**: {datetime.fromisoformat(trace['timestamp']).strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                )
                f.write(f"- **Tool Name**: {trace['tool_name']}\n")
                f.write(
                    f"- **Status**: {'SUCCESS' if trace.get('error_state') is None else 'FAILED'}\n"
                )
                f.write(
                    f"- **Execution Time**: {trace['execution_time']:.2f} seconds\n"
                )
                f.write(f"- **Confidence Score**: {trace['confidence_score']:.2f}\n")
                if trace.get("error_state"):
                    f.write(f"- **Error**: {trace['error_state']}\n")
                f.write(
                    f"- **Inputs**:\n```json\n{json.dumps(trace.get('inputs', {}), indent=2)}\n```\n"
                )
                f.write(
                    f"- **Outputs**:\n```json\n{json.dumps(trace.get('outputs', {}), indent=2)}\n```\n"
                )
        typer.echo(f"Traces exported to {output} in Markdown format.")
    else:
        typer.echo("Error: Unsupported export format. Choose from 'csv', 'json', 'md'.")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
