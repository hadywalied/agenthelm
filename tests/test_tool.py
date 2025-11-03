import pytest
from orchestrator.core.tool import tool, TOOL_REGISTRY


# Clean up the registry before each test to ensure isolation
@pytest.fixture(autouse=True)
def clear_tool_registry():
    TOOL_REGISTRY.clear()


def test_tool_registration_and_introspection():
    """Tests that the @tool decorator correctly registers a function and introspects its inputs."""

    @tool(outputs={"status": "str"})
    def my_test_tool(name: str, count: int):
        """A simple test tool."""
        return f"Hello, {name}"

    # 1. Check if the tool is in the registry
    assert "my_test_tool" in TOOL_REGISTRY

    # 2. Check if the function itself is stored correctly
    assert TOOL_REGISTRY["my_test_tool"]["function"] == my_test_tool.__wrapped__

    # 3. Check if the contract was created
    contract = TOOL_REGISTRY["my_test_tool"]["contract"]
    assert contract is not None

    # 4. Check if the inputs were correctly introspected
    expected_inputs = {"name": "str", "count": "int"}
    assert contract["inputs"] == expected_inputs

    # 5. Check if the manually provided outputs are correct
    assert contract["outputs"] == {"status": "str"}
