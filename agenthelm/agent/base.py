from abc import ABC, abstractmethod
from typing import Callable

import dspy

from agenthelm import MemoryHub, ExecutionTracer, TOOL_REGISTRY


class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
        lm: dspy.LM,
        tools: list[Callable] | None = None,
        memory: MemoryHub | None = None,
        tracer: ExecutionTracer | None = None,
    ):
        self.name = name
        self.lm = lm
        self.tools = tools or []
        self.memory = memory
        self.tracer = tracer

    @abstractmethod
    def run(self, task: str): ...

    def _execute_tool(self, tool: str | Callable, *args, **kwargs):
        tool_func = tool if callable(tool) else None
        if tool_func is None and tool in TOOL_REGISTRY:
            tool_func = TOOL_REGISTRY[tool]["function"]
        if tool_func is None:
            raise RuntimeError(f"tool {tool} is not supported")
        if self.tracer:
            output, event = self.tracer.trace_and_execute(tool_func, *args, **kwargs)
            return output, event
        else:
            return tool_func(*args, **kwargs), None

    async def _remember(self, text) -> str | None:
        """Store text in semantic memory. Returns memory ID or None if no memory."""
        if self.memory:
            return await self.memory.semantic.store(text)
        return None

    async def _recall(self, query) -> list:
        """Search semantic memory. Returns empty list if no memory."""
        if self.memory:
            return await self.memory.semantic.search(query)
        return []
