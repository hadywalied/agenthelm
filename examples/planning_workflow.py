"""
Planning Workflow Example

Demonstrates generating and executing multi-step plans.
"""

import dspy
from agenthelm import PlannerAgent, Plan, tool


# Define tools that might be used in plans
@tool()
def research(topic: str) -> str:
    """Research a topic and return findings."""
    return f"Research findings about {topic}: Key insights and data points gathered."


@tool()
def write_draft(content: str) -> str:
    """Write a draft based on content."""
    return f"Draft written based on: {content[:50]}..."


@tool()
def review(draft: str) -> str:
    """Review a draft and provide feedback."""
    return "Review complete. Draft looks good with minor suggestions."


@tool()
def publish(final_content: str) -> str:
    """Publish the final content."""
    return "Published successfully!"


def main():
    # Configure LLM
    lm = dspy.LM("mistral/mistral-large-latest")

    # Create planner
    planner = PlannerAgent(
        name="content_planner",
        lm=lm,
        tools=[research, write_draft, review, publish],
    )

    # Generate a plan
    task = "Write and publish a blog post about AI agents"
    print(f"Task: {task}")
    print("=" * 50)

    plan = planner.plan(task)

    # Display the plan
    print(f"\nGoal: {plan.goal}")
    print(f"Reasoning: {plan.reasoning}\n")

    print("Steps:")
    for step in plan.steps:
        deps = f" (depends on: {', '.join(step.depends_on)})" if step.depends_on else ""
        print(f"  {step.id}: {step.tool_name} - {step.description}{deps}")

    # Save plan to file
    plan_yaml = plan.to_yaml()
    print("\n--- Plan YAML ---")
    print(plan_yaml)

    # Save to file
    with open("example_plan.yaml", "w") as f:
        f.write(plan_yaml)
    print("\n✓ Plan saved to example_plan.yaml")

    # Load plan from file
    with open("example_plan.yaml", "r") as f:
        loaded_plan = Plan.from_yaml(f.read())
    print(f"✓ Loaded plan with {len(loaded_plan.steps)} steps")


if __name__ == "__main__":
    main()
