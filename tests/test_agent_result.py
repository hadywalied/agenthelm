"""Tests for agenthelm.agent - AgentResult model."""

from datetime import datetime, timezone

import pytest

from agenthelm.agent.result import AgentResult
from agenthelm.core.event import Event, TokenUsage


class TestAgentResult:
    """Tests for AgentResult model."""

    def test_create_empty_result(self):
        """Create an empty result."""
        result = AgentResult(success=False)
        assert not result.success
        assert result.answer is None
        assert result.error is None
        assert result.events == []
        assert result.total_cost_usd == 0.0

    def test_successful_result(self):
        """Create a successful result."""
        result = AgentResult(
            success=True,
            answer="The weather is sunny.",
            session_id="test-session",
            iterations=3,
        )
        assert result.success
        assert result.answer == "The weather is sunny."
        assert result.session_id == "test-session"
        assert result.iterations == 3

    def test_failed_result(self):
        """Create a failed result."""
        result = AgentResult(
            success=False,
            error="Tool execution failed",
        )
        assert not result.success
        assert result.error == "Tool execution failed"

    def test_add_event(self):
        """Add events to result."""
        result = AgentResult(success=True)

        event = Event(
            timestamp=datetime.now(timezone.utc),
            tool_name="get_weather",
            inputs={"city": "NYC"},
            outputs={"result": "sunny"},
            execution_time=0.5,
            estimated_cost_usd=0.001,
            token_usage=TokenUsage(input_tokens=100, output_tokens=50),
        )

        result.add_event(event)

        assert len(result.events) == 1
        assert result.total_cost_usd == 0.001
        assert result.token_usage.input_tokens == 100
        assert result.token_usage.output_tokens == 50

    def test_add_multiple_events(self):
        """Cost and tokens are aggregated across events."""
        result = AgentResult(success=True)

        event1 = Event(
            timestamp=datetime.now(timezone.utc),
            tool_name="search",
            inputs={},
            outputs={},
            execution_time=0.2,
            estimated_cost_usd=0.002,
            token_usage=TokenUsage(input_tokens=100, output_tokens=50),
        )
        event2 = Event(
            timestamp=datetime.now(timezone.utc),
            tool_name="summarize",
            inputs={},
            outputs={},
            execution_time=0.3,
            estimated_cost_usd=0.003,
            token_usage=TokenUsage(input_tokens=200, output_tokens=100),
        )

        result.add_event(event1)
        result.add_event(event2)

        assert len(result.events) == 2
        assert result.total_cost_usd == pytest.approx(0.005)
        assert result.token_usage.input_tokens == 300
        assert result.token_usage.output_tokens == 150

    def test_add_event_without_cost(self):
        """Events without cost don't break aggregation."""
        result = AgentResult(success=True)

        event = Event(
            timestamp=datetime.now(timezone.utc),
            tool_name="local_tool",
            inputs={},
            outputs={},
            execution_time=0.1,
        )

        result.add_event(event)
        assert result.total_cost_usd == 0.0
