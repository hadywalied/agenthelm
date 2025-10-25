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

    def trace_and_execute(self, tool_func: Callable, *args, **kwargs):
        pargs = inspect.signature(tool_func).bind(*args, **kwargs).arguments
        timestamp = datetime.now(timezone.utc)
        start_time = time.monotonic()
        output = None
        error_state = None
        contract = TOOL_REGISTRY.get(tool_func.__name__, {}).get('contract', {})
        requires_approval = contract.get('requires_approval', False)
        if requires_approval:
            user_approval = self.approval_handler.request_approval(tool_func.__name__, pargs)
            if not user_approval:
                error_state = "User did not approve execution."
                execution_time = time.monotonic() - start_time
                event = Event(timestamp=timestamp,
                              tool_name=tool_func.__name__,
                              inputs=pargs,
                              outputs={},
                              execution_time=execution_time,
                              error_state=error_state)
                self.storage.save(event.model_dump())
                return None
        try:
            output = tool_func(*args, **kwargs)
        except Exception as e:
            error_state = str(e)

        execution_time = time.monotonic() - start_time

        # The output dictionary for the event should be created after the call
        outputs_dict = {}
        if error_state is None:
            outputs_dict = {"result": output}

        event = Event(timestamp=timestamp,
                      tool_name=tool_func.__name__,
                      inputs=pargs,
                      outputs=outputs_dict,
                      execution_time=execution_time,
                      error_state=error_state)

        self.storage.save(event.model_dump())
        return output
