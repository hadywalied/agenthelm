"""
AgentHelm - A production-ready, observable, and reliable AI agent orchestration framework.

This is the public API package. Users import from here.
Internally, this re-exports everything from the `orchestrator` package.
"""

__version__ = "0.1.2"

# Re-export core components from orchestrator
from orchestrator.agent import Agent
from orchestrator.core.tool import tool, TOOL_REGISTRY
from orchestrator.core.tracer import ExecutionTracer
from orchestrator.core.storage import FileStorage, Storage
from orchestrator.core.event import Event

# Re-export LLM clients
from orchestrator.llm.base import LLMClient
from orchestrator.llm.mistral_client import MistralClient
from orchestrator.llm.openai_client import OpenAIClient

__all__ = [
    "Agent",
    "tool",
    "TOOL_REGISTRY",
    "ExecutionTracer",
    "FileStorage",
    "Storage",
    "Event",
    "LLMClient",
    "MistralClient",
    "OpenAIClient",
]


def cli_main():
    """Entry point for the CLI command."""
    from orchestrator.cli import app

    app()
