from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime


class Event(BaseModel):
    """
    timestamp: When the event happened.
    tool_name: The name of the tool that was called.
    inputs: The arguments the tool was called with.
    outputs: What the tool returned.
    execution_time: How long it took to run.
    error_state: Any error that occurred, or null if it succeeded.
    llm_reasoning_trace: (For now, this can be a placeholder string).
    confidence_score: (For now, this can be a placeholder float, like 1.0).
    """

    timestamp: datetime
    tool_name: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    execution_time: float
    error_state: Optional[str] = None
    llm_reasoning_trace: str = "placeholder"
    confidence_score: float = 1.0
