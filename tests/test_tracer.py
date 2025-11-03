import pytest
from orchestrator.core.tool import tool, TOOL_REGISTRY
from orchestrator.core.tracer import ExecutionTracer
from orchestrator.core.storage import FileStorage
from orchestrator.core.handlers import ApprovalHandler
import os

# --- Test Fixtures ---


@pytest.fixture(autouse=True)
def clear_tool_registry():
    """Ensures the TOOL_REGISTRY is empty before each test."""
    TOOL_REGISTRY.clear()


@pytest.fixture
def tracer() -> ExecutionTracer:
    """Provides a tracer instance with an in-memory storage for testing."""
    if os.path.exists("test_trace.json"):
        os.remove("test_trace.json")
    storage = FileStorage("test_trace.json")
    return ExecutionTracer(storage=storage)


# --- Mock Components ---


class MockApprovalHandler(ApprovalHandler):
    def __init__(self, approve: bool):
        self.approve = approve
        self.called = False

    def request_approval(self, tool_name: str, arguments: dict) -> bool:
        self.called = True
        return self.approve


# --- Test Cases ---


def test_tracer_requires_approval_approved(tracer):
    """Tests that the tracer executes a tool when approval is given."""
    tracer.approval_handler = MockApprovalHandler(approve=True)

    @tool(requires_approval=True)
    def sensitive_tool():
        return "success"

    result = tracer.trace_and_execute(sensitive_tool)
    assert result == "success"
    assert tracer.approval_handler.called is True


def test_tracer_requires_approval_denied(tracer):
    """Tests that the tracer stops execution when approval is denied."""
    handler = MockApprovalHandler(approve=False)
    tracer.approval_handler = handler

    @tool(requires_approval=True)
    def sensitive_tool():
        return "success"

    # Assert that the correct exception is raised
    with pytest.raises(RuntimeError, match="User did not approve execution."):
        tracer.trace_and_execute(sensitive_tool)

    # Assert that the handler was still called
    assert handler.called is True

    # Check the trace log to ensure denial was recorded
    log = tracer.storage.load()
    assert len(log) == 1
    assert log[0]["error_state"] == "User did not approve execution."


def test_tracer_retries_succeeds():
    """Tests the retry logic for a tool that eventually succeeds."""
    # Separate storage and tracer for this test to isolate the log
    if os.path.exists("retry_test_trace.json"):
        os.remove("retry_test_trace.json")
    storage = FileStorage("retry_test_trace.json")
    tracer = ExecutionTracer(storage=storage)

    class FlakyState:
        attempts = 0

    state = FlakyState()

    @tool(retries=2)  # 3 total attempts
    def flaky_tool_for_test():
        state.attempts += 1
        if state.attempts < 3:
            raise ValueError("Failing intentionally")
        return "success"

    result = tracer.trace_and_execute(flaky_tool_for_test)

    assert state.attempts == 3
    assert result == "success"

    # The log should only contain the final, successful event
    log = tracer.storage.load()
    assert len(log) == 1
    assert log[0]["error_state"] is None
    assert log[0]["tool_name"] == "flaky_tool_for_test"
