"""
Tracing and Observability Example

Demonstrates execution tracing, cost tracking, and OpenTelemetry integration.
"""

import dspy
from agenthelm import ToolAgent, tool, ExecutionTracer
from agenthelm.core.storage import SqliteStorage


# Define tools
@tool()
def calculate(expression: str) -> float:
    """Evaluate a mathematical expression."""
    # Simple safe eval for demo
    allowed = set("0123456789+-*/.(). ")
    if all(c in allowed for c in expression):
        return eval(expression)
    return 0.0


@tool()
def lookup(key: str) -> str:
    """Look up a value by key."""
    data = {
        "pi": "3.14159",
        "e": "2.71828",
        "golden_ratio": "1.61803",
    }
    return data.get(key, "Not found")


def main():
    # Configure LLM
    lm = dspy.LM("mistral/mistral-large-latest")

    # Setup tracing with SQLite storage
    storage = SqliteStorage("observability_traces.db")
    tracer = ExecutionTracer(storage=storage)

    # Optional: Enable OpenTelemetry for Jaeger
    # Uncomment to send traces to Jaeger (requires: docker run -p 16686:16686 -p 4317:4317 jaegertracing/all-in-one)
    # init_tracing(service_name="example-app", otlp_endpoint="http://localhost:4317", enabled=True)

    # Create agent
    agent = ToolAgent(
        name="math_agent",
        lm=lm,
        tools=[calculate, lookup],
        tracer=tracer,
        max_iters=5,
    )

    # Run tasks
    tasks = [
        "What is the value of pi?",
        "Calculate 25 * 4 + 10",
        "What is 100 / 5?",
    ]

    print("Running tasks with tracing...")
    print("=" * 50)

    for task in tasks:
        print(f"\nTask: {task}")

        # Optional: Wrap with OpenTelemetry span
        # with trace_agent("math_agent", task=task):
        result = agent.run(task)

        if result.success:
            print(f"✓ {result.answer}")
        else:
            print(f"✗ {result.error}")

        # Show metrics
        if result.token_usage:
            print(
                f"  Tokens: {result.token_usage.input_tokens + result.token_usage.output_tokens}"
            )
        if result.total_cost_usd > 0:
            print(f"  Cost: ${result.total_cost_usd:.4f}")
        print(f"  Events: {len(result.events)}")

    # Show trace summary
    print("\n" + "=" * 50)
    print("Trace Summary")
    print("=" * 50)

    events = storage.load()
    print(f"Total traced events: {len(events)}")

    for e in events[-5:]:  # Show last 5
        status = "OK" if not e.get("error_state") else "FAILED"
        print(f"  {e.get('tool_name')}: {status} ({e.get('execution_time', 0):.3f}s)")

    print("\n✓ Traces saved to: observability_traces.db")
    print("  View with: agenthelm traces list -s observability_traces.db")


if __name__ == "__main__":
    main()
