import logging
import inspect
import time
import uuid
from datetime import datetime, timezone
from typing import Callable

from agenthelm.core.event import Event
from agenthelm.core.handlers import ApprovalHandler, CliHandler
from agenthelm.core.storage.base import BaseStorage
from agenthelm.core.tool import TOOL_REGISTRY


class ExecutionTracer:
    def __init__(
        self,
        storage: BaseStorage,
        approval_handler: ApprovalHandler | None = None,
        session_id: str | None = None,
    ):
        self.storage = storage
        self.approval_handler = approval_handler or CliHandler()
        self.session_id = session_id or str(uuid.uuid4())

        # Context for next trace
        self._current_reasoning: str | None = None
        self._current_confidence: float = 1.0
        self._current_agent_name: str | None = None

    def set_trace_context(
        self,
        reasoning: str,
        confidence: float,
        agent_name: str | None = None,
    ):
        """Sets the LLM reasoning context for the next trace event."""
        self._current_reasoning = reasoning
        self._current_confidence = confidence
        self._current_agent_name = agent_name

    def trace_and_execute(self, tool_func: Callable, *args, **kwargs):
        pargs = inspect.signature(tool_func).bind(*args, **kwargs).arguments
        timestamp = datetime.now(timezone.utc)
        start_time = time.monotonic()
        output = None
        error_state = None
        retry_count = 0
        trace_id = str(uuid.uuid4())  # Unique ID for this execution

        try:
            contract = TOOL_REGISTRY.get(tool_func.__name__, {}).get("contract", {})
            requires_approval = contract.get("requires_approval", False)
            if requires_approval:
                user_approval = self.approval_handler.request_approval(
                    tool_func.__name__, pargs
                )
                if not user_approval:
                    raise PermissionError("User did not approve execution.")

            retries = contract.get("retries", 0)
            for attempt in range(retries + 1):
                try:
                    output = tool_func(*args, **kwargs)
                    error_state = None  # Reset error state on success
                    break  # If successful, exit the loop
                except Exception as e:
                    error_state = str(e)
                    retry_count = attempt + 1
                    logging.warning(
                        f"Attempt {attempt + 1}/{retries + 1} failed: {error_state}"
                    )
                    if attempt < retries:
                        time.sleep(1)  # Wait 1 second before the next attempt

            if error_state:
                raise RuntimeError(error_state)

        except Exception as e:
            error_state = str(e)

        execution_time = time.monotonic() - start_time
        outputs_dict = {"result": output} if error_state is None else {}

        event = Event(
            timestamp=timestamp,
            tool_name=tool_func.__name__,
            inputs=pargs,
            outputs=outputs_dict,
            execution_time=execution_time,
            error_state=error_state,
            llm_reasoning_trace=self._current_reasoning or "",
            confidence_score=self._current_confidence,
            # New v0.3.0 fields
            retry_count=retry_count,
            agent_name=self._current_agent_name,
            session_id=self.session_id,
            trace_id=trace_id,
        )

        # Clear the context for the next run
        self._current_reasoning = None
        self._current_confidence = 1.0
        self._current_agent_name = None

        self.storage.save(event.model_dump())

        if error_state:
            raise RuntimeError(error_state)

        return output, event
