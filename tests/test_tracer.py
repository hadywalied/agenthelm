"""Tests for agenthelm.core.tracer - ExecutionTracer."""

import pytest
from unittest.mock import MagicMock

from agenthelm import ExecutionTracer, tool, TOOL_REGISTRY, Event
from agenthelm.core.handlers import AutoApproveHandler, AutoDenyHandler
from agenthelm.core.storage.base import BaseStorage


class MockStorage(BaseStorage):
    """In-memory storage for testing."""

    def __init__(self):
        self.events: list[dict] = []

    def save(self, event: dict) -> None:
        self.events.append(event)

    def load(self) -> list[dict]:
        return self.events

    def query(self, filters=None) -> list[dict]:
        return self.events


class TestExecutionTracerBasic:
    """Test basic ExecutionTracer functionality."""

    def setup_method(self):
        TOOL_REGISTRY.clear()
        self.storage = MockStorage()
        self.tracer = ExecutionTracer(
            storage=self.storage,
            approval_handler=AutoApproveHandler(),
        )

    def test_tracer_has_session_id(self):
        """Tracer should have a session_id."""
        assert self.tracer.session_id is not None
        assert len(self.tracer.session_id) > 0

    def test_custom_session_id(self):
        """Tracer should accept custom session_id."""
        tracer = ExecutionTracer(
            storage=self.storage,
            session_id="my-custom-session",
        )
        assert tracer.session_id == "my-custom-session"

    def test_trace_and_execute_saves_event(self):
        """trace_and_execute should save an event to storage."""

        @tool()
        def simple_tool(x: int) -> int:
            return x * 2

        result, event = self.tracer.trace_and_execute(simple_tool, x=5)

        assert result == 10
        assert event is not None
        assert len(self.storage.events) == 1

        event = self.storage.events[0]
        assert event["tool_name"] == "simple_tool"
        assert event["inputs"] == {"x": 5}
        assert event["outputs"] == {"result": 10}
        assert event["error_state"] is None

    def test_trace_and_execute_captures_error(self):
        """trace_and_execute should capture errors."""

        @tool()
        def failing_tool() -> str:
            raise ValueError("Something went wrong")

        with pytest.raises(RuntimeError, match="Something went wrong"):
            self.tracer.trace_and_execute(failing_tool)

        assert len(self.storage.events) == 1
        event = self.storage.events[0]
        assert "Something went wrong" in event["error_state"]

    def test_trace_and_execute_records_execution_time(self):
        """trace_and_execute should record execution time."""

        @tool()
        def slow_tool() -> str:
            import time

            time.sleep(0.1)
            return "done"

        self.tracer.trace_and_execute(slow_tool)

        event = self.storage.events[0]
        assert event["execution_time"] >= 0.08  # Allow timing variance

    def test_event_has_trace_id(self):
        """Each execution should have a unique trace_id."""

        @tool()
        def my_tool() -> str:
            return "ok"

        self.tracer.trace_and_execute(my_tool)
        self.tracer.trace_and_execute(my_tool)

        trace_id_1 = self.storage.events[0]["trace_id"]
        trace_id_2 = self.storage.events[1]["trace_id"]

        assert trace_id_1 is not None
        assert trace_id_2 is not None
        assert trace_id_1 != trace_id_2

    def test_event_has_session_id(self):
        """Events should have the tracer's session_id."""

        @tool()
        def my_tool() -> str:
            return "ok"

        self.tracer.trace_and_execute(my_tool)

        event = self.storage.events[0]
        assert event["session_id"] == self.tracer.session_id


class TestExecutionTracerContext:
    """Test trace context (reasoning, confidence, agent)."""

    def setup_method(self):
        TOOL_REGISTRY.clear()
        self.storage = MockStorage()
        self.tracer = ExecutionTracer(
            storage=self.storage,
            approval_handler=AutoApproveHandler(),
        )

    def test_set_trace_context(self):
        """set_trace_context should set reasoning and confidence."""

        @tool()
        def my_tool() -> str:
            return "ok"

        self.tracer.set_trace_context(
            reasoning="Decided to use this tool because...",
            confidence=0.85,
            agent_name="researcher",
        )
        self.tracer.trace_and_execute(my_tool)

        event = self.storage.events[0]
        assert event["llm_reasoning_trace"] == "Decided to use this tool because..."
        assert event["confidence_score"] == 0.85
        assert event["agent_name"] == "researcher"

    def test_context_is_cleared_after_execution(self):
        """Context should be cleared after execution."""

        @tool()
        def my_tool() -> str:
            return "ok"

        self.tracer.set_trace_context(reasoning="First", confidence=0.9)
        self.tracer.trace_and_execute(my_tool)

        # Second execution without setting context
        self.tracer.trace_and_execute(my_tool)

        event1 = self.storage.events[0]
        event2 = self.storage.events[1]

        assert event1["llm_reasoning_trace"] == "First"
        assert event2["llm_reasoning_trace"] == ""  # Cleared


class TestExecutionTracerRetry:
    """Test retry logic."""

    def setup_method(self):
        TOOL_REGISTRY.clear()
        self.storage = MockStorage()
        self.tracer = ExecutionTracer(
            storage=self.storage,
            approval_handler=AutoApproveHandler(),
        )

    def test_retry_on_failure(self):
        """Tool with retries should retry on failure."""
        call_count = 0

        @tool(retries=2)
        def flaky_tool() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result, event = self.tracer.trace_and_execute(flaky_tool)

        assert result == "success"
        assert call_count == 3  # 1 initial + 2 retries

    def test_retry_count_in_event(self):
        """Event should record retry count."""
        call_count = 0

        @tool(retries=1)
        def flaky_tool() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Fail once")
            return "ok"

        self.tracer.trace_and_execute(flaky_tool)

        event = self.storage.events[0]
        assert "retry_count" in event

    def test_exhausted_retries_raises(self):
        """Should raise after exhausting retries."""

        @tool(retries=2)
        def always_fails() -> str:
            raise ValueError("Always fails")

        with pytest.raises(RuntimeError, match="Always fails"):
            self.tracer.trace_and_execute(always_fails)


class TestExecutionTracerApproval:
    """Test approval flow."""

    def setup_method(self):
        TOOL_REGISTRY.clear()
        self.storage = MockStorage()

    def test_auto_approve_handler(self):
        """AutoApproveHandler should allow execution."""
        tracer = ExecutionTracer(
            storage=self.storage,
            approval_handler=AutoApproveHandler(),
        )

        @tool(requires_approval=True)
        def dangerous_tool() -> str:
            return "executed"

        result, event = tracer.trace_and_execute(dangerous_tool)
        assert result == "executed"

    def test_auto_deny_handler(self):
        """AutoDenyHandler should block execution."""
        tracer = ExecutionTracer(
            storage=self.storage,
            approval_handler=AutoDenyHandler(),
        )

        @tool(requires_approval=True)
        def dangerous_tool() -> str:
            return "executed"

        with pytest.raises(RuntimeError, match="did not approve"):
            tracer.trace_and_execute(dangerous_tool)

    def test_no_approval_needed_skips_handler(self):
        """Tool without requires_approval should skip approval."""
        mock_handler = MagicMock()
        mock_handler.request_approval.return_value = True

        tracer = ExecutionTracer(
            storage=self.storage,
            approval_handler=mock_handler,
        )

        @tool(requires_approval=False)
        def safe_tool() -> str:
            return "ok"

        tracer.trace_and_execute(safe_tool)

        mock_handler.request_approval.assert_not_called()


class TestExecutionTracerIntegration:
    """Integration tests with real Event model."""

    def setup_method(self):
        TOOL_REGISTRY.clear()
        self.storage = MockStorage()
        self.tracer = ExecutionTracer(
            storage=self.storage,
            approval_handler=AutoApproveHandler(),
        )

    def test_event_is_valid_model(self):
        """Saved event should be a valid Event model dict."""

        @tool()
        def my_tool(name: str) -> str:
            return f"Hello, {name}"

        self.tracer.trace_and_execute(my_tool, name="World")

        event_dict = self.storage.events[0]

        event = Event(**event_dict)
        assert event.tool_name == "my_tool"
        assert event.inputs == {"name": "World"}
        assert event.outputs == {"result": "Hello, World"}
