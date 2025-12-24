"""PlannerAgent - Generates execution plans for tasks."""

import json
from typing import Callable

import dspy

from agenthelm import MemoryHub, ExecutionTracer
from agenthelm.agent.base import BaseAgent
from agenthelm.agent.plan import Plan, PlanStep


class PlannerAgent(BaseAgent):
    """
    Agent that generates structured execution plans.

    The PlannerAgent creates plans but does NOT execute them.
    Execution is handled by the Orchestrator (Week 4).
    """

    def __init__(
        self,
        name: str,
        lm: dspy.LM,
        tools: list[Callable] | None = None,
        memory: MemoryHub | None = None,
        tracer: ExecutionTracer | None = None,
        role: str | None = None,
        max_steps: int = 10,
    ):
        super().__init__(name, lm, tools, memory, tracer, role)
        self.max_steps = max_steps

        # DSPy module for plan generation - include role if provided
        if self.role:
            self._planning = dspy.ChainOfThought(
                "task, available_tools, role -> goal, reasoning, steps_json"
            )
        else:
            self._planning = dspy.ChainOfThought(
                "task, available_tools -> goal, reasoning, steps_json"
            )

    def _get_tool_descriptions(self) -> str:
        """Get tool names and descriptions for the LLM."""
        tool_info = []
        for tool in self.tools:
            tool_info.append(
                {
                    "name": tool.__name__,
                    "description": tool.__doc__ or "No description",
                }
            )
        return json.dumps(tool_info, indent=2)

    def _parse_steps(self, steps_json: str) -> list[PlanStep]:
        """Parse LLM-generated steps JSON into PlanStep objects."""
        try:
            # Try to parse as JSON
            steps_data = json.loads(steps_json)
        except json.JSONDecodeError:
            # If not valid JSON, try to extract from markdown code block
            if "```json" in steps_json:
                start = steps_json.find("```json") + 7
                end = steps_json.find("```", start)
                steps_json = steps_json[start:end].strip()
                steps_data = json.loads(steps_json)
            elif "```" in steps_json:
                start = steps_json.find("```") + 3
                end = steps_json.find("```", start)
                steps_json = steps_json[start:end].strip()
                steps_data = json.loads(steps_json)
            else:
                raise ValueError(f"Could not parse steps: {steps_json}")

        if not isinstance(steps_data, list):
            steps_data = [steps_data]

        parsed_steps = []
        for i, step in enumerate(steps_data):
            parsed_steps.append(
                PlanStep(
                    id=step.get("id", f"step_{i + 1}"),
                    agent_name=step.get("agent_name") or step.get("agent"),
                    tool_name=step.get("tool_name") or step.get("tool", ""),
                    description=step.get("description", ""),
                    args=step.get("args", {}),
                    depends_on=step.get("depends_on", []),
                )
            )
        return parsed_steps

    def plan(self, task: str) -> Plan:
        """
        Generate an execution plan for the given task.

        Args:
            task: The task to plan for

        Returns:
            Plan object with steps (not yet executed)
        """
        tool_descriptions = self._get_tool_descriptions()

        with dspy.context(lm=self.lm):
            if self.role:
                result = self._planning(
                    task=task,
                    available_tools=tool_descriptions,
                    role=self.role,
                )
            else:
                result = self._planning(
                    task=task,
                    available_tools=tool_descriptions,
                )

        # Parse the steps from LLM output
        steps = self._parse_steps(result.steps_json)

        return Plan(
            goal=result.goal,
            reasoning=result.reasoning,
            steps=steps,
        )

    def run(self, task: str) -> Plan:
        """Generate a plan (alias for plan())."""
        return self.plan(task)
