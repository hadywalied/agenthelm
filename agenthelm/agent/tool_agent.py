from typing import Callable

import dspy

from agenthelm.agent.result import AgentResult
from agenthelm import MemoryHub, ExecutionTracer
from agenthelm.agent.base import BaseAgent


class ToolAgent(BaseAgent):
    """
    ReAct-style agent that reasons and executes tools.

    Uses DSPy's ReAct pattern to iteratively:
    1. Reason about the task
    2. Choose and execute a tool
    3. Observe the result
    4. Repeat until done
    """

    def __init__(
        self,
        name: str,
        lm: dspy.LM,
        tools: list[Callable] | None = None,
        memory: MemoryHub | None = None,
        tracer: ExecutionTracer | None = None,
        role: str | None = None,
        max_iters: int = 10,
    ):
        super().__init__(name, lm, tools, memory, tracer, role)
        self.max_iters = max_iters

        # Build signature with optional role context
        if self.role:
            signature = "task, role -> answer"
        else:
            signature = "task -> answer"

        self._react = dspy.ReAct(
            signature=signature,
            tools=self._wrap_tools_for_tracing(),
            max_iters=self.max_iters,
        )
        self._events = []

    def run(self, task: str) -> AgentResult:
        """Execute the ReAct loop and return results with traced events."""
        self._events = []  # Reset events for this run
        result = AgentResult(success=False, session_id=self.name)
        try:
            with dspy.context(lm=self.lm):
                if self.role:
                    react_result = self._react(task=task, role=self.role)
                else:
                    react_result = self._react(task=task)

            result.success = True
            result.answer = react_result.answer

        except Exception as e:
            result.success = False
            result.error = str(e)

        # Collect events from tracer if available
        for event in self._events:
            result.add_event(event)

        return result

    def _wrap_tools_for_tracing(self) -> list[Callable]:
        """Wrap tools to trace through ExecutionTracer."""
        wrapped_tools = []
        for tool in self.tools:
            # Use default arg to capture current tool value
            def traced_tool(*args, _tool=tool, **kwargs):
                output, event = self._execute_tool(_tool, *args, **kwargs)
                if event:
                    self._events.append(event)
                return output

            traced_tool.__name__ = tool.__name__
            traced_tool.__doc__ = tool.__doc__
            wrapped_tools.append(traced_tool)
        return wrapped_tools
