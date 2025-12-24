"""Orchestrator - Executes plans by routing steps to agents."""

import asyncio
import logging
from typing import Any

from agenthelm.agent.base import BaseAgent
from agenthelm.agent.plan import Plan, PlanStep, StepStatus
from agenthelm.agent.result import AgentResult
from agenthelm.core.event import Event
from agenthelm.core.tool import TOOL_REGISTRY
from agenthelm.orchestration.registry import AgentRegistry

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Executes plans by routing steps to registered agents.

    Supports:
    - Sequential execution (steps with dependencies)
    - Parallel execution (independent steps)
    - Saga pattern: rollback on failure via compensating actions
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
        enable_rollback: bool = True,
    ):
        """
        Initialize orchestrator.

        Args:
            registry: Registry of named agents
            default_agent: Fallback agent for steps without agent_name
            enable_rollback: If True, run compensating actions on failure
        """
        self.registry = registry
        self.default_agent = default_agent
        self.enable_rollback = enable_rollback

    async def execute(self, plan: Plan) -> AgentResult:
        """
        Execute a plan by routing steps to agents.

        On failure, if enable_rollback is True, runs compensating actions
        for completed steps in reverse order (Saga pattern).

        Args:
            plan: The plan to execute

        Returns:
            AgentResult with aggregated events and metrics
        """
        if not plan.approved:
            raise ValueError("Plan must be approved before execution")

        result = AgentResult(success=False)
        all_events: list[Event] = []
        failed = False

        while not plan.is_complete:
            ready_steps = plan.get_ready_steps()

            if not ready_steps:
                # No steps ready but plan not complete - deadlock
                result.error = "Plan execution deadlock: no steps ready"
                failed = True
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
                    failed = True
                else:
                    output, events = step_result
                    plan.mark_completed(step.id, result=output)
                    all_events.extend(events)

            # On first failure, break and rollback
            if failed:
                break

        # Saga: rollback completed steps on failure
        if failed and self.enable_rollback:
            rollback_events = await self._rollback(plan)
            all_events.extend(rollback_events)

        # Build final result
        result.success = plan.success
        for event in all_events:
            result.add_event(event)

        if not result.success and not result.error:
            failed_steps = [s for s in plan.steps if s.status == StepStatus.FAILED]
            if failed_steps:
                result.error = f"Steps failed: {[s.id for s in failed_steps]}"

        return result

    async def _rollback(self, plan: Plan) -> list[Event]:
        """
        Run compensating actions for completed steps in reverse order.

        Compensation priority:
        1. Step-level compensate_tool (if set)
        2. Tool-level compensating_tool from TOOL_REGISTRY

        Args:
            plan: The plan to rollback

        Returns:
            List of events from compensation actions
        """
        events: list[Event] = []
        completed = [s for s in plan.steps if s.status == StepStatus.COMPLETED]

        for step in reversed(completed):
            compensate_tool = self._get_compensate_tool(step)

            if not compensate_tool:
                logger.debug(f"No compensating action for step {step.id}")
                continue

            try:
                logger.info(f"Rolling back step {step.id} with {compensate_tool}")
                compensate_args = step.compensate_args or step.args

                # Build compensation task
                agent = self._get_agent_for_step(step)
                task = f"Compensate: {compensate_tool} with args {compensate_args}"

                agent_result = agent.run(task)
                events.extend(agent_result.events)

            except Exception as e:
                logger.error(f"Rollback failed for step {step.id}: {e}")
                # Continue rolling back other steps

        return events

    def _get_compensate_tool(self, step: PlanStep) -> str | None:
        """Get the compensating tool for a step (step-level overrides tool-level)."""
        # Step-level override
        if step.compensate_tool:
            return step.compensate_tool

        # Tool-level default from registry
        tool_info = TOOL_REGISTRY.get(step.tool_name, {})
        contract = tool_info.get("contract", {})
        return contract.get("compensating_tool")

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
