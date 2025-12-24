"""
Basic Agent Example

Demonstrates creating a ToolAgent with custom tools.
"""

import dspy
from agenthelm import ToolAgent, tool, ExecutionTracer
from agenthelm.core.storage import SqliteStorage


# Define tools
@tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


@tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b


@tool()
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    weather_data = {
        "New York": "Sunny, 24°C",
        "London": "Cloudy, 15°C",
        "Tokyo": "Rainy, 18°C",
    }
    return weather_data.get(city, f"Weather data not available for {city}")


def main():
    # Configure LLM
    lm = dspy.LM("mistral/mistral-large-latest")

    # Create tracer for observability
    storage = SqliteStorage("example_traces.db")
    tracer = ExecutionTracer(storage=storage)

    # Create agent with tools
    agent = ToolAgent(
        name="assistant",
        lm=lm,
        tools=[add, multiply, get_weather],
        tracer=tracer,
        max_iters=5,
    )

    # Run tasks
    tasks = [
        "What is 15 + 27?",
        "What is 8 multiplied by 6?",
        "What's the weather in Tokyo?",
    ]

    for task in tasks:
        print(f"\n{'=' * 50}")
        print(f"Task: {task}")
        print("=" * 50)

        result = agent.run(task)

        if result.success:
            print(f"✓ Answer: {result.answer}")
        else:
            print(f"✗ Error: {result.error}")

        # Show token usage
        if result.token_usage:
            total = result.token_usage.input_tokens + result.token_usage.output_tokens
            print(f"  Tokens: {total}")


if __name__ == "__main__":
    main()
