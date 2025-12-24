"""Tests for agenthelm.core.cost - CostTracker and TokenUsage."""

import pytest
import tempfile
import os

from agenthelm import CostTracker, TokenOnlyCostTracker, get_cost_tracker
from agenthelm.core.cost import TokenUsage


class TestTokenUsage:
    """Test TokenUsage model."""

    def test_token_usage_creation(self):
        """TokenUsage should be created with required fields."""
        usage = TokenUsage(input_tokens=100, output_tokens=50, model="gpt-4o")
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.model == "gpt-4o"

    def test_token_usage_total_tokens(self):
        """TokenUsage should calculate total tokens."""
        usage = TokenUsage(input_tokens=100, output_tokens=200, model="gpt-4o")
        assert usage.total_tokens == 300


class TestCostTracker:
    """Test CostTracker with pricing."""

    def test_default_pricing(self):
        """CostTracker should have default pricing."""
        tracker = CostTracker()
        assert "gpt-4o" in tracker.pricing
        assert "claude-3-5-sonnet" in tracker.pricing

    def test_track_returns_cost(self):
        """track() should return estimated cost."""
        tracker = CostTracker()
        usage = TokenUsage(input_tokens=1_000_000, output_tokens=0, model="gpt-4o")
        cost = tracker.track(usage)
        # gpt-4o input is $2.50 per 1M tokens
        assert cost == pytest.approx(2.50, abs=0.01)

    def test_track_accumulates(self):
        """Multiple tracks should accumulate."""
        tracker = CostTracker()
        usage1 = TokenUsage(input_tokens=500_000, output_tokens=0, model="gpt-4o")
        usage2 = TokenUsage(input_tokens=500_000, output_tokens=0, model="gpt-4o")

        tracker.track(usage1)
        tracker.track(usage2)

        assert tracker.get_total_cost() == pytest.approx(2.50, abs=0.01)
        assert tracker.get_total_tokens() == 1_000_000

    def test_check_budget(self):
        """check_budget should return True if under budget."""
        tracker = CostTracker()
        usage = TokenUsage(input_tokens=100, output_tokens=50, model="gpt-4o")
        tracker.track(usage)

        assert tracker.check_budget(max_cost=1.0) is True
        assert tracker.check_budget(max_cost=0.00001) is False

    def test_custom_pricing(self):
        """CostTracker should accept custom pricing."""
        custom_pricing = {"my-model": {"input": 5.0, "output": 10.0}}
        tracker = CostTracker(pricing=custom_pricing)
        usage = TokenUsage(input_tokens=1_000_000, output_tokens=0, model="my-model")
        cost = tracker.track(usage)
        assert cost == pytest.approx(5.0, abs=0.01)

    def test_model_normalization(self):
        """CostTracker should normalize model names."""
        tracker = CostTracker()
        # Test with prefix
        price = tracker.get_price("openai/gpt-4o")
        assert price["input"] == pytest.approx(2.50, abs=0.1)

    def test_get_summary(self):
        """get_summary should return usage stats."""
        tracker = CostTracker()
        usage = TokenUsage(input_tokens=100, output_tokens=200, model="gpt-4o")
        tracker.track(usage)

        summary = tracker.get_summary()
        assert summary["total_input_tokens"] == 100
        assert summary["total_output_tokens"] == 200
        assert summary["total_tokens"] == 300
        assert summary["num_calls"] == 1

    def test_reset(self):
        """reset() should clear all counters."""
        tracker = CostTracker()
        usage = TokenUsage(input_tokens=100, output_tokens=200, model="gpt-4o")
        tracker.track(usage)

        tracker.reset()

        assert tracker.get_total_tokens() == 0
        assert tracker.get_total_cost() == 0.0
        assert len(tracker.usages) == 0


class TestTokenOnlyCostTracker:
    """Test TokenOnlyCostTracker (no cost calculation)."""

    def test_track_returns_zero(self):
        """TokenOnlyCostTracker.track() should return 0."""
        tracker = TokenOnlyCostTracker()
        usage = TokenUsage(
            input_tokens=1_000_000, output_tokens=500_000, model="gpt-4o"
        )
        cost = tracker.track(usage)
        assert cost == 0.0

    def test_total_cost_is_zero(self):
        """get_total_cost should always return 0."""
        tracker = TokenOnlyCostTracker()
        usage = TokenUsage(input_tokens=1000, output_tokens=500, model="gpt-4o")
        tracker.track(usage)
        assert tracker.get_total_cost() == 0.0

    def test_tracks_tokens(self):
        """TokenOnlyCostTracker should still track tokens."""
        tracker = TokenOnlyCostTracker()
        usage = TokenUsage(input_tokens=100, output_tokens=200, model="gpt-4o")
        tracker.track(usage)
        assert tracker.get_total_tokens() == 300


class TestGetCostTracker:
    """Test factory function."""

    def test_default_returns_cost_tracker(self):
        """get_cost_tracker() should return CostTracker by default."""
        tracker = get_cost_tracker()
        assert isinstance(tracker, CostTracker)

    def test_tokens_only_flag(self):
        """get_cost_tracker(tokens_only=True) should return TokenOnlyCostTracker."""
        tracker = get_cost_tracker(tokens_only=True)
        assert isinstance(tracker, TokenOnlyCostTracker)

    def test_custom_pricing_passed(self):
        """get_cost_tracker should pass pricing to CostTracker."""
        custom = {"test-model": {"input": 1.0, "output": 2.0}}
        tracker = get_cost_tracker(pricing=custom)
        assert "test-model" in tracker.pricing


class TestCostTrackerFromFile:
    """Test loading pricing from YAML file."""

    def test_from_yaml_file(self):
        """CostTracker should load pricing from YAML."""
        yaml_content = """
pricing:
  custom-model:
    input: 1.23
    output: 4.56
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            path = f.name

        try:
            tracker = CostTracker.from_config(path)
            assert "custom-model" in tracker.pricing
            assert tracker.pricing["custom-model"]["input"] == 1.23
        finally:
            os.unlink(path)
