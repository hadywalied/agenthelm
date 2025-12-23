"""Agent execution result models."""

from pydantic import BaseModel, Field

from agenthelm.core.event import Event, TokenUsage


class AgentResult(BaseModel):
    """
    Result of an agent execution.

    Contains the final answer, execution events, and cost/token metrics.
    """

    success: bool = Field(description="Whether the agent completed successfully")
    answer: str | None = Field(default=None, description="Final answer from the agent")
    error: str | None = Field(default=None, description="Error message if failed")

    # Execution trace
    events: list[Event] = Field(default_factory=list, description="All tool executions")

    # Cost and token tracking
    total_cost_usd: float = Field(default=0.0, description="Total estimated cost")
    token_usage: TokenUsage = Field(
        default_factory=lambda: TokenUsage(input_tokens=0, output_tokens=0),
        description="Aggregated token usage",
    )

    # Metadata
    session_id: str | None = Field(default=None, description="Session identifier")
    iterations: int = Field(default=0, description="Number of reasoning iterations")

    def add_event(self, event: Event) -> None:
        """Add an event and update aggregated metrics."""
        self.events.append(event)
        if event.estimated_cost_usd:
            self.total_cost_usd += event.estimated_cost_usd
        if event.token_usage:
            self.token_usage = TokenUsage(
                input_tokens=self.token_usage.input_tokens
                + event.token_usage.input_tokens,
                output_tokens=self.token_usage.output_tokens
                + event.token_usage.output_tokens,
                model=event.token_usage.model or self.token_usage.model,
            )
