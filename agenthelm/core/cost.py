from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
import yaml

from pydantic import BaseModel


class TokenUsage(BaseModel):
    """Token usage from an LLM call."""

    input_tokens: int
    output_tokens: int
    model: str | None = None

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class BaseCostTracker(ABC):
    """Abstract base class for cost tracking."""

    @abstractmethod
    def track(self, usage: TokenUsage) -> float:
        """Track usage and return estimated cost for this call."""
        ...

    @abstractmethod
    def get_total_cost(self) -> float:
        """Get total accumulated cost."""
        ...

    @abstractmethod
    def get_total_tokens(self) -> int:
        """Get total tokens used."""
        ...

    def check_budget(self, max_cost: float) -> bool:
        """Check if within budget."""
        return self.get_total_cost() <= max_cost


class TokenOnlyCostTracker(BaseCostTracker):
    """Tracks token usage only, no cost calculation."""

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.usages: list[TokenUsage] = []

    def track(self, usage: TokenUsage) -> float:
        self.total_input_tokens += usage.input_tokens
        self.total_output_tokens += usage.output_tokens
        self.usages.append(usage)
        return 0.0  # No cost tracking

    def get_total_cost(self) -> float:
        return 0.0

    def get_total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens


class CostTracker(BaseCostTracker):
    """Tracks token usage and estimates costs based on pricing table."""

    # Default pricing per 1M tokens (USD, approximate 2025/2026)
    DEFAULT_PRICING: dict[str, dict[str, float]] = {
        # OpenAI
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "o1": {"input": 15.00, "output": 60.00},
        "o1-mini": {"input": 3.00, "output": 12.00},
        # Anthropic
        "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
        "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
        "claude-3-opus": {"input": 15.00, "output": 75.00},
        # Mistral
        "mistral-large": {"input": 2.00, "output": 6.00},
        "mistral-small": {"input": 0.20, "output": 0.60},
        "codestral": {"input": 0.20, "output": 0.60},
        "mistral-nemo": {"input": 0.15, "output": 0.15},
        # Google
        "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
        # Chinese / OpenRouter
        "deepseek-chat": {"input": 0.14, "output": 0.28},
        "deepseek-coder": {"input": 0.14, "output": 0.28},
        "qwen-72b": {"input": 0.50, "output": 1.50},
        "qwen-32b": {"input": 0.25, "output": 0.75},
    }

    def __init__(
        self,
        pricing: dict[str, dict[str, float]] | None = None,
        pricing_file: str | Path | None = None,
    ):
        """
        Initialize CostTracker.

        Args:
            pricing: Custom pricing dict {model: {input: $, output: $}} per 1M tokens
            pricing_file: Path to YAML file with pricing config
        """
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.usages: list[TokenUsage] = []

        # Load pricing (priority: pricing_file > pricing > DEFAULT_PRICING)
        if pricing_file:
            self.pricing = self._load_pricing_file(pricing_file)
        elif pricing:
            self.pricing = pricing
        else:
            self.pricing = self.DEFAULT_PRICING.copy()

    @classmethod
    def from_config(cls, config_path: str | Path) -> "CostTracker":
        """Create CostTracker from a YAML config file."""
        return cls(pricing_file=config_path)

    def _load_pricing_file(self, path: str | Path) -> dict[str, dict[str, float]]:
        """Load pricing from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return data.get("pricing", data)

    def _normalize_model_name(self, model: str) -> str:
        """Normalize model name for lookup (handle aliases, prefixes)."""
        # Remove common prefixes
        model = model.lower()
        for prefix in ["openai/", "anthropic/", "mistral/", "google/", "openrouter/"]:
            if model.startswith(prefix):
                model = model[len(prefix) :]

        # Handle date suffixes like gpt-4o-2024-08-06
        parts = model.split("-")
        if len(parts) >= 3 and parts[-1].isdigit():
            # Remove date suffix
            model = "-".join(parts[:-3]) if len(parts) > 3 else "-".join(parts[:-1])

        return model

    def get_price(self, model: str) -> dict[str, float]:
        """Get pricing for a model, returns default if not found."""
        normalized = self._normalize_model_name(model)

        # Try exact match first
        if normalized in self.pricing:
            return self.pricing[normalized]

        # Try partial match
        for key in self.pricing:
            if key in normalized or normalized in key:
                return self.pricing[key]

        # Fallback to a reasonable default
        return {"input": 1.00, "output": 3.00}

    def track(self, usage: TokenUsage) -> float:
        """Track usage and return estimated cost for this call."""
        self.total_input_tokens += usage.input_tokens
        self.total_output_tokens += usage.output_tokens
        self.usages.append(usage)

        # Calculate cost
        price = self.get_price(usage.model)
        input_cost = (usage.input_tokens / 1_000_000) * price["input"]
        output_cost = (usage.output_tokens / 1_000_000) * price["output"]
        call_cost = input_cost + output_cost

        self.total_cost += call_cost
        return call_cost

    def get_total_cost(self) -> float:
        return self.total_cost

    def get_total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of usage and costs."""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.get_total_tokens(),
            "total_cost_usd": round(self.total_cost, 6),
            "num_calls": len(self.usages),
        }

    def reset(self):
        """Reset all counters."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.usages.clear()


# =============================================================================
# Factory Function
# =============================================================================


def get_cost_tracker(
    tokens_only: bool = False,
    pricing: dict[str, dict[str, float]] | None = None,
    pricing_file: str | Path | None = None,
) -> BaseCostTracker:
    """
    Factory function to create the appropriate CostTracker.

    Args:
        tokens_only: If True, returns TokenOnlyCostTracker (no cost calculation)
        pricing: Custom pricing dict (only used if tokens_only=False)
        pricing_file: Path to YAML pricing config (only used if tokens_only=False)

    Returns:
        BaseCostTracker instance

    Examples:
        >>> tracker = get_cost_tracker()  # Full tracking with default pricing
        >>> tracker = get_cost_tracker(tokens_only=True)  # Token counting only
        >>> tracker = get_cost_tracker(pricing_file="my_pricing.yaml")
    """
    if tokens_only:
        return TokenOnlyCostTracker()
    else:
        return CostTracker(pricing=pricing, pricing_file=pricing_file)
