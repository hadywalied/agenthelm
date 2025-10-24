import inspect
import time
from datetime import datetime, timezone
from typing import Callable

from .storage import FileStorage
from .event import Event


class ExecutionTracer:
    def __init__(self, storage: FileStorage):
        self.storage = storage

    def trace_and_execute(self, tool_func: Callable, *args, kwargs):
        pargs = inspect.signature(tool_func).bind(*args, **kwargs).arguments
        timestamp = datetime.now(timezone.utc)
        start_time = time.monotonic()
        error_state = None
        outputs_dict = {'result': None}
        try:
            output = tool_func(*args, **kwargs)
            outputs_dict = {"result": output}
        except Exception as e:
            error_state = str(e)

        execution_time = time.monotonic() - start_time

        event = Event(timestamp=timestamp,
                      tool_name=tool_func.__name__,
                      inputs=pargs,
                      outputs=outputs_dict,
                      execution_time=execution_time,
                      error_state=error_state)

        self.storage.save(event.model_dump())
        return output
