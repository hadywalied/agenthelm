import logging
import inspect
import time
from datetime import datetime, timezone
from typing import Callable

from orchestrator.core.tool import TOOL_REGISTRY
from orchestrator.core.handlers import CliHandler, ApprovalHandler

from .storage import FileStorage
from .event import Event


class ExecutionTracer:
    def __init__(self, storage: FileStorage, approval_handler: ApprovalHandler = None):
        self.storage = storage
        self.approval_handler = approval_handler or CliHandler()
        self._current_reasoning = None
        self._current_confidence = 1.0

    def set_trace_context(self, reasoning: str, confidence: float):
        """Sets the LLM reasoning context for the next trace event."""
        self._current_reasoning = reasoning
        self._current_confidence = confidence

    def trace_and_execute(self, tool_func: Callable, *args, **kwargs):
        pargs = inspect.signature(tool_func).bind(*args, **kwargs).arguments
        timestamp = datetime.now(timezone.utc)
        start_time = time.monotonic()
        output = None
        error_state = None

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
        )

        # Clear the context for the next run
        self._current_reasoning = None
        self._current_confidence = 1.0

        self.storage.save(event.model_dump())

        if error_state:
            raise RuntimeError(error_state)

        return output
