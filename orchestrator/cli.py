"""Command-line interface for AgentHelm."""

from enum import Enum
import typer
import os
import importlib.util
import inspect
import logging
from typing import List, Callable

from orchestrator.core.storage import FileStorage
from orchestrator.core.tool import TOOL_REGISTRY
from orchestrator.core.tracer import ExecutionTracer
from orchestrator.agent import Agent
from orchestrator.llm.mistral_client import MistralClient
from orchestrator.llm.openai_client import OpenAIClient


class LLM_TYPE(str, Enum):
    MISTRAL = "mistral"
    OPENAI = "openai"


app = typer.Typer(help="A CLI for running and observing AI agents.")


@app.callback()
def main(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose DEBUG-level logging."
    ),
):
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(message)s")
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
    storage = FileStorage("cli_trace.json")
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


if __name__ == "__main__":
    app()
