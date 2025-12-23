"""Tests for agenthelm.core.tool - Tool decorator and registry."""

from agenthelm import tool, TOOL_REGISTRY


class TestToolDecorator:
    """Test the @tool decorator."""

    def setup_method(self):
        """Clear registry before each test."""
        TOOL_REGISTRY.clear()

    def test_tool_registers_function(self):
        """Tool decorator should register function in TOOL_REGISTRY."""

        @tool()
        def my_tool(arg: str) -> str:
            return arg

        assert "my_tool" in TOOL_REGISTRY
        assert callable(TOOL_REGISTRY["my_tool"]["function"])
        assert TOOL_REGISTRY["my_tool"]["function"].__name__ == "my_tool"

    def test_tool_infers_inputs_from_type_hints(self):
        """Tool decorator should infer inputs from function type hints."""

        @tool()
        def my_tool(name: str, count: int) -> str:
            return f"{name}: {count}"

        contract = TOOL_REGISTRY["my_tool"]["contract"]
        assert contract["inputs"] == {"name": "str", "count": "int"}

    def test_tool_infers_outputs_from_return_type(self):
        """Tool decorator should infer outputs from return type hint."""

        @tool()
        def my_tool() -> str:
            return "hello"

        contract = TOOL_REGISTRY["my_tool"]["contract"]
        assert contract["outputs"] == {"result": "str"}

    def test_tool_stores_contract_fields(self):
        """Tool decorator should store all contract fields."""

        @tool(
            side_effects=["file:write"],
            max_cost=0.5,
            requires_approval=True,
            retries=3,
            compensating_tool="undo_tool",
            timeout=60.0,
            tags=["io", "dangerous"],
        )
        def risky_tool(path: str) -> dict:
            return {"path": path}

        contract = TOOL_REGISTRY["risky_tool"]["contract"]
        assert contract["side_effects"] == ["file:write"]
        assert contract["max_cost"] == 0.5
        assert contract["requires_approval"] is True
        assert contract["retries"] == 3
        assert contract["compensating_tool"] == "undo_tool"
        assert contract["timeout"] == 60.0
        assert contract["tags"] == ["io", "dangerous"]

    def test_tool_default_values(self):
        """Tool decorator should have sensible defaults."""

        @tool()
        def simple_tool(x: int) -> int:
            return x * 2

        contract = TOOL_REGISTRY["simple_tool"]["contract"]
        assert contract["side_effects"] == []
        assert contract["max_cost"] == 0.0
        assert contract["requires_approval"] is False
        assert contract["retries"] == 0
        assert contract["compensating_tool"] is None
        assert contract["timeout"] == 30.0

    def test_tool_function_still_executes(self):
        """Decorated function should still work normally."""

        @tool()
        def add(a: int, b: int) -> int:
            return a + b

        result = add(2, 3)
        assert result == 5


class TestToolRegistry:
    """Test TOOL_REGISTRY functionality."""

    def setup_method(self):
        TOOL_REGISTRY.clear()

    def test_registry_is_dict(self):
        """TOOL_REGISTRY should be a dictionary."""
        assert isinstance(TOOL_REGISTRY, dict)

    def test_multiple_tools_registered(self):
        """Multiple tools should be registered independently."""

        @tool()
        def tool_a() -> str:
            return "a"

        @tool()
        def tool_b() -> str:
            return "b"

        assert "tool_a" in TOOL_REGISTRY
        assert "tool_b" in TOOL_REGISTRY
        assert len(TOOL_REGISTRY) == 2
