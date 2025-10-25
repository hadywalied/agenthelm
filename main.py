from enum import Enum

import typer
import os
import importlib.util
import inspect
from typing import List, Callable

from build.lib.orchestrator.llm.openai_client import OpenAIClient
from orchestrator.core.storage import FileStorage
from orchestrator.core.tool import TOOL_REGISTRY, tool
from orchestrator.core.tracer import ExecutionTracer
from orchestrator.agent import Agent
from orchestrator.llm.mistral_client import MistralClient


class LLM_TYPE(Enum):
    MISTRAL = "mistral"
    OPENAI = "openai"


app = typer.Typer(help="A CLI for running and observing AI agents.")


@app.command()
def help():
    """Display a custom help message for the DockAI CLI."""
    typer.echo("Welcome to DockAI - The Docker for AI Agents")
    typer.echo("This tool allows you to run AI agents with observable, debuggable, and reliable execution.")
    typer.echo("\nAvailable commands:")
    typer.echo("  run: Execute an agent with a given set of tools and a task.")
    typer.echo("\nTo get help for a specific command, use: python main.py [COMMAND] --help")
    typer.echo("Example: python main.py run --help")


def load_tools_from_file(filepath: str) -> List[Callable]:
    """Dynamically loads a Python file and discovers functions decorated with @tool."""

    # Create a unique module name to avoid conflicts
    module_name = f"agent_tools.{os.path.basename(filepath).replace('.py', '')}"

    spec = importlib.util.spec_from_file_location(module_name, filepath)
    if not spec or not spec.loader:
        raise ImportError(f"Could not load spec from {filepath}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Discover functions in the module that are in our TOOL_REGISTRY
    discovered_tools = []
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and name in TOOL_REGISTRY:
            discovered_tools.append(obj)

    return discovered_tools


@app.command()
def run(llm_type: LLM_TYPE = typer.Option(LLM_TYPE.MISTRAL,
                                            help="The type of LLM to use. choose between mistral and openai for now."),
        agent_file: str = typer.Option(..., help="The path to the Python file containing tool definitions."),
        task: str = typer.Option(..., help="The natural language task for the agent to perform."),
        max_steps: int = typer.Option(10, help="The maximum number of steps to run the agent for.")):
    """Runs the agent with a specified set of tools and a task."""

    typer.echo(f"Loading tools from: {agent_file}")
    try:
        agent_tools = load_tools_from_file(agent_file)
        if not agent_tools:
            typer.echo(f"Error: No tools found in {agent_file}. Make sure your functions are decorated with @tool.")
            raise typer.Exit(code=1)
        typer.echo(f"Found {len(agent_tools)} tools: {[t.__name__ for t in agent_tools]}")
    except Exception as e:
        typer.echo(f"Error loading tools file: {e}")
        raise typer.Exit(code=1)

    # 1. Setup the components
    storage = FileStorage('cli_trace.json')
    tracer = ExecutionTracer(storage)

    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        typer.echo("Error: MISTRAL_API_KEY environment variable not set.")
        raise typer.Exit(code=1)

    match llm_type:
        case LLM_TYPE.MISTRAL:
            model_name = os.environ.get("MISTRAL_MODEL_NAME", "mistral-small-latest")
            typer.echo(
                f"Using MISTRAL model: {model_name}"
            )
            client = MistralClient(model_name=model_name, api_key=api_key)
        case LLM_TYPE.OPENAI:
            model_name = os.environ.get("OPENAI_MODEL_NAME", "gpt-5")
            typer.echo(
                f"Using OPENAI model: {model_name}"
            )
            client = OpenAIClient(model_name=model_name, api_key=api_key)
        case _:
            typer.echo(f"Unsupported LLM type: {llm_type}")
            raise typer.Exit(code=1)

    # 2. Instantiate the Agent
    agent = Agent(tools=agent_tools, tracer=tracer, client=client)

    # 3. Run the agent with the task
    typer.echo(f"\nRunning agent with task: '{task}'")
    agent.run_react(task, max_steps)

    typer.echo("\nAgent run finished.")


if __name__ == "__main__":
    app()
