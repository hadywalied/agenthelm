"""
AgentHelm - A production-ready, observable, and reliable AI agent orchestration framework.
"""

__version__ = "0.1.2"

# Core imports
from orchestrator.agent import Agent
from orchestrator.core.tool import tool, TOOL_REGISTRY
from orchestrator.core.tracer import ExecutionTracer
from orchestrator.core.storage import FileStorage, Storage
from orchestrator.core.event import Event
from orchestrator.core.handlers import CliHandler, ApprovalHandler

# LLM clients
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
    "CliHandler",
    "ApprovalHandler",
]
