"""
AgentHelm Orchestration Module - Multi-agent plan execution.

Example usage:
    from agenthelm.orchestration import AgentRegistry, Orchestrator

    # Register agents
    registry = AgentRegistry()
    registry.register(researcher)
    registry.register(writer)

    # Execute a plan
    orchestrator = Orchestrator(registry)
    result = await orchestrator.execute(plan)
"""

from agenthelm.orchestration.registry import AgentRegistry
from agenthelm.orchestration.orchestrator import Orchestrator

__all__ = [
    "AgentRegistry",
    "Orchestrator",
]
