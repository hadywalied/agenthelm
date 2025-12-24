"""
AgentHelm v0.3.0
================

A DSPy-native multi-agent orchestration framework.
"""

from agenthelm.core import (
    tool,
    TOOL_REGISTRY,
    Event,
    TokenUsage,
    ApprovalHandler,
    CliHandler,
    AutoApproveHandler,
    AutoDenyHandler,
    ExecutionTracer,
    BaseCostTracker,
    CostTracker,
    TokenOnlyCostTracker,
    get_cost_tracker,
)

from agenthelm.memory import (
    MemoryHub,
    MemoryContext,
    BaseShortTermMemory,
    BaseSemanticMemory,
    InMemoryShortTermMemory,
    SqliteShortTermMemory,
    SemanticMemory,
    SearchResult,
)

from agenthelm.agent import (
    BaseAgent,
    AgentResult,
    Plan,
    PlanStep,
    StepStatus,
    ToolAgent,
    PlannerAgent,
)

from agenthelm.orchestration import (
    AgentRegistry,
    Orchestrator,
)
from agenthelm.mcp import MCPClient, MCPToolAdapter
from agenthelm.tracing import (
    init_tracing,
    get_tracer,
    trace_tool,
    trace_agent,
)

__version__ = "0.3.0"

__all__ = [
    "__version__",
    # Core
    "tool",
    "TOOL_REGISTRY",
    "Event",
    "TokenUsage",
    "ApprovalHandler",
    "CliHandler",
    "AutoApproveHandler",
    "AutoDenyHandler",
    "ExecutionTracer",
    "BaseCostTracker",
    "CostTracker",
    "TokenOnlyCostTracker",
    "get_cost_tracker",
    # Memory Hub
    "MemoryHub",
    "MemoryContext",
    "BaseShortTermMemory",
    "BaseSemanticMemory",
    "InMemoryShortTermMemory",
    "SqliteShortTermMemory",
    "SemanticMemory",
    "SearchResult",
    # Agents
    "BaseAgent",
    "AgentResult",
    "Plan",
    "PlanStep",
    "StepStatus",
    "ToolAgent",
    "PlannerAgent",
    # Orchestration
    "AgentRegistry",
    "Orchestrator",
    # MCP
    "MCPClient",
    "MCPToolAdapter",
    # Tracing
    "init_tracing",
    "get_tracer",
    "trace_tool",
    "trace_agent",
]
