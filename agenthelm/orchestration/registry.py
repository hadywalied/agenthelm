"""AgentRegistry - Named agent container for multi-agent orchestration."""

from typing import Iterator

from agenthelm.agent.base import BaseAgent


class AgentRegistry:
    """
    Registry for named agents.

    Allows registering and looking up agents by name for orchestration.

    Example:
        registry = AgentRegistry()
        registry.register(researcher_agent)
        registry.register(writer_agent)

        agent = registry["researcher"]
        agent.run("Find information about...")
    """

    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        """
        Register an agent by its name.

        Args:
            agent: Agent to register (uses agent.name as key)

        Raises:
            ValueError: If agent with same name already registered
        """
        if agent.name in self._agents:
            raise ValueError(f"Agent '{agent.name}' already registered")
        self._agents[agent.name] = agent

    def unregister(self, name: str) -> BaseAgent | None:
        """
        Remove an agent from the registry.

        Args:
            name: Name of agent to remove

        Returns:
            The removed agent, or None if not found
        """
        return self._agents.pop(name, None)

    def get(self, name: str) -> BaseAgent | None:
        """Get an agent by name, returns None if not found."""
        return self._agents.get(name)

    def __getitem__(self, name: str) -> BaseAgent:
        """Get an agent by name, raises KeyError if not found."""
        if name not in self._agents:
            raise KeyError(f"Agent '{name}' not found in registry")
        return self._agents[name]

    def __contains__(self, name: str) -> bool:
        """Check if an agent is registered."""
        return name in self._agents

    def __iter__(self) -> Iterator[str]:
        """Iterate over agent names."""
        return iter(self._agents)

    def __len__(self) -> int:
        """Number of registered agents."""
        return len(self._agents)

    @property
    def names(self) -> list[str]:
        """List of all registered agent names."""
        return list(self._agents.keys())

    def clear(self) -> None:
        """Remove all agents from registry."""
        self._agents.clear()
