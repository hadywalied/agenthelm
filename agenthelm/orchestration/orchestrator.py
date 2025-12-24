"""Orchestrator - Executes plans by routing steps to agents."""

import asyncio
from typing import Any

from agenthelm.agent.base import BaseAgent
from agenthelm.agent.plan import Plan, PlanStep, StepStatus
from agenthelm.agent.result import AgentResult
from agenthelm.core.event import Event
from agenthelm.orchestration.registry import AgentRegistry


class Orchestrator:
    """
    Executes plans by routing steps to registered agents.

    Supports:
    - Sequential execution (steps with dependencies)
    - Parallel execution (independent steps)
    - Error handling and step failure tracking

    Example:
        registry = AgentRegistry()
        registry.register(researcher)
        registry.register(writer)

        orchestrator = Orchestrator(registry)
        result = await orchestrator.execute(plan)
    """

    def __init__(
        self,
        registry: AgentRegistry,
        default_agent: BaseAgent | None = None,
    ):
        """
        Initialize orchestrator.

        Args:
            registry: Registry of named agents
            default_agent: Fallback agent for steps without agent_name
        """
        self.registry = registry
        self.default_agent = default_agent

    async def execute(self, plan: Plan) -> AgentResult:
        """
        Execute a plan by routing steps to agents.

        Args:
            plan: The plan to execute

        Returns:
            AgentResult with aggregated events and metrics
        """
        if not plan.approved:
            raise ValueError("Plan must be approved before execution")

        result = AgentResult(success=False)
        all_events: list[Event] = []

        while not plan.is_complete:
            ready_steps = plan.get_ready_steps()

            if not ready_steps:
                # No steps ready but plan not complete - deadlock
                result.error = "Plan execution deadlock: no steps ready"
                break

            # Execute ready steps in parallel
            step_results = await asyncio.gather(
                *[self._execute_step(step) for step in ready_steps],
                return_exceptions=True,
            )

            # Process results
            for step, step_result in zip(ready_steps, step_results):
                if isinstance(step_result, Exception):
                    plan.mark_failed(step.id, str(step_result))
                else:
                    output, events = step_result
                    plan.mark_completed(step.id, result=output)
                    all_events.extend(events)

        # Build final result
        result.success = plan.success
        for event in all_events:
            result.add_event(event)

        if not result.success and not result.error:
            failed_steps = [s for s in plan.steps if s.status == StepStatus.FAILED]
            if failed_steps:
                result.error = f"Steps failed: {[s.id for s in failed_steps]}"

        return result

    async def _execute_step(self, step: PlanStep) -> tuple[Any, list[Event]]:
        """
        Execute a single plan step.

        Args:
            step: The step to execute

        Returns:
            Tuple of (result, events)
        """
        step.status = StepStatus.RUNNING

        # Find the agent to execute this step
        agent = self._get_agent_for_step(step)

        # Build the task from step description and args
        task = self._build_task(step)

        # Execute via agent
        agent_result = agent.run(task)

        if not agent_result.success:
            raise RuntimeError(agent_result.error or "Agent execution failed")

        return agent_result.answer, agent_result.events

    def _get_agent_for_step(self, step: PlanStep) -> BaseAgent:
        """Get the appropriate agent for a step."""
        if step.agent_name:
            if step.agent_name in self.registry:
                return self.registry[step.agent_name]
            raise ValueError(f"Agent '{step.agent_name}' not found in registry")

        if self.default_agent:
            return self.default_agent

        raise ValueError(
            f"Step '{step.id}' has no agent_name and no default_agent configured"
        )

    def _build_task(self, step: PlanStep) -> str:
        """Build a task string from step information."""
        if step.args:
            args_str = ", ".join(f"{k}={v}" for k, v in step.args.items())
            return f"{step.description} (args: {args_str})"
        return step.description

    async def execute_sync(self, plan: Plan) -> AgentResult:
        """Synchronous wrapper for execute()."""
        return await self.execute(plan)


5
