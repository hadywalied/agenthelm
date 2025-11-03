import pytest
import os
from orchestrator.core.tool import tool, TOOL_REGISTRY
from orchestrator.core.tracer import ExecutionTracer
from orchestrator.core.storage import FileStorage
from orchestrator.agent import Agent
from orchestrator.llm.base import LLMClient


# --- Test Fixtures ---


@pytest.fixture(autouse=True)
def clear_tool_registry():
    TOOL_REGISTRY.clear()


# --- Mock LLM Client ---


class MockLLMClient(LLMClient):
    """A mock LLM client that returns pre-programmed responses."""

    def __init__(self, responses: list):
        self.responses = responses
        super().__init__("mock-model", "", "")

    def predict(self, system_prompt: str, user_prompt: str) -> str:
        if not self.responses:
            pytest.fail("MockLLMClient received more requests than expected.")
        return self.responses.pop(0)


# --- Test Cases for the Agent ---


def test_agent_react_loop_success():
    """Tests a successful multi-step workflow using the ReAct agent."""
    # 1. Setup
    storage = FileStorage("test_react_success.json")
    if os.path.exists("test_react_success.json"):
        os.remove("test_react_success.json")
    tracer = ExecutionTracer(storage=storage)

    @tool()
    def get_user_name(user_id: int) -> str:
        """Gets the name of a user from their ID."""
        if user_id == 123:
            return "Alice"
        return "Unknown"

    # Program the LLM's responses
    mock_llm = MockLLMClient(
        responses=[
            """json
        {
            "tool_name": "get_user_name",
            "arguments": {"user_id": 123}
        }
        """,
            """json
        {
            "tool_name": "finish",
            "arguments": {"answer": "The user's name is Alice."}
        }
        """,
        ]
    )

    agent = Agent(tools=[get_user_name], tracer=tracer, client=mock_llm)

    # 2. Execution
    result = agent.run_react("What is the name of user 123?")

    # 3. Assertions
    assert result["status"] == "Workflow succeeded."
    assert result["final_answer"] == "The user's name is Alice."
    log = storage.load()
    assert len(log) == 1
    assert log[0]["tool_name"] == "get_user_name"


def test_agent_react_loop_rollback():
    """Tests that the agent correctly performs a rollback on failure."""
    # 1. Setup
    storage = FileStorage("test_react_rollback.json")
    if os.path.exists("test_react_rollback.json"):
        os.remove("test_react_rollback.json")
    tracer = ExecutionTracer(storage=storage)

    # Define tools with a compensator
    @tool()
    def undo_action(arg: str):
        print(f"COMPENSATED: {arg}")
        return {"undone": True}

    @tool(compensating_tool="undo_action")
    def do_action(arg: str):
        return {"result": f"did {arg}"}

    @tool()
    def failing_tool():
        raise ValueError("This failed intentionally")

    # Program the LLM's responses
    mock_llm = MockLLMClient(
        responses=[
            """json
        {"tool_name": "do_action", "arguments": {"arg": "step 1"}}
        """,
            """json
        {"tool_name": "failing_tool", "arguments": {}}
        """,
            """json
        {"tool_name": "undo_action", "arguments": {}}
        """,
        ]
    )

    agent = Agent(
        tools=[do_action, undo_action, failing_tool], tracer=tracer, client=mock_llm
    )

    # 2. Execution
    result = agent.run_react("Do an action then fail.")

    # 3. Assertions
    assert result["status"] == "Workflow failed and was rolled back."
    log = storage.load()
    assert len(log) == 3
    assert log[0]["tool_name"] == "do_action"
    assert log[0]["error_state"] is None
    assert log[1]["tool_name"] == "failing_tool"
    assert log[1]["error_state"] is not None
    assert log[2]["tool_name"] == "undo_action"  # The compensator was run
    assert log[2]["error_state"] is None
