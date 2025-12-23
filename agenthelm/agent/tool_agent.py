from typing import Callable

import dspy

from agenthelm.agent.result import AgentResult
from agenthelm import MemoryHub, ExecutionTracer
from agenthelm.agent.base import BaseAgent


class ToolAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        lm: dspy.LM,
        tools: list[Callable] | None = None,
        memory: MemoryHub | None = None,
        tracer: ExecutionTracer | None = None,
        max_iters=10,
    ):
        super().__init__(name, lm, tools, memory, tracer)
        self.max_iters = max_iters

        self._react = dspy.ReAct(
            signature="task -> answer",
            tools=self._wrap_tools_for_tracing(),
            max_iters=self.max_iters,
        )
        self._events = []

    def run(self, task: str) -> AgentResult:
        """Execute the ReAct loop and return results with traced events."""
        result = AgentResult(success=False, session_id=self.name)
        try:
            with dspy.context(lm=self.lm):
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
