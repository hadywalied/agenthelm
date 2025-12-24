"""
Multi-Agent Orchestration Example

Demonstrates multiple agents working together with the Orchestrator.
"""

import dspy
from agenthelm import (
    ToolAgent,
    AgentRegistry,
    Orchestrator,
    Plan,
    PlanStep,
    StepStatus,
    tool,
)


# Researcher tools
@tool()
def search_web(query: str) -> str:
    """Search the web for information."""
    return f"Search results for '{query}': Found 10 relevant articles about the topic."


@tool()
def analyze_data(data: str) -> str:
    """Analyze data and extract insights."""
    return "Analysis complete. Key insights: The data shows positive trends."


# Writer tools
@tool()
def write_article(topic: str, research: str) -> str:
    """Write an article based on research."""
    return f"Article about {topic} written based on research findings."


@tool()
def edit_article(article: str) -> str:
    """Edit and polish an article."""
    return "Article edited and polished for publication."


def main():
    # Configure LLM
    lm = dspy.LM("mistral/mistral-large-latest")

    # Create specialized agents
    researcher = ToolAgent(
        name="researcher",
        lm=lm,
        tools=[search_web, analyze_data],
        role="You are a research specialist who finds and analyzes information.",
    )

    writer = ToolAgent(
        name="writer",
        lm=lm,
        tools=[write_article, edit_article],
        role="You are a content writer who creates polished articles.",
    )

    # Register agents
    registry = AgentRegistry()
    registry.register("researcher", researcher)
    registry.register("writer", writer)

    print("Registered agents:", registry.list())

    # Create a multi-step plan
    plan = Plan(
        goal="Research AI agents and write an article",
        reasoning="Need to research first, then write based on findings",
        steps=[
            PlanStep(
                id="step1",
                tool_name="search_web",
                description="Search for AI agent information",
                agent_name="researcher",
                args={"query": "AI agents 2024"},
            ),
            PlanStep(
                id="step2",
                tool_name="analyze_data",
                description="Analyze the search results",
                agent_name="researcher",
                depends_on=["step1"],
                args={"data": "Search results"},
            ),
            PlanStep(
                id="step3",
                tool_name="write_article",
                description="Write article based on research",
                agent_name="writer",
                depends_on=["step2"],
                args={"topic": "AI Agents", "research": "Analysis results"},
            ),
            PlanStep(
                id="step4",
                tool_name="edit_article",
                description="Polish the article",
                agent_name="writer",
                depends_on=["step3"],
                args={"article": "Draft article"},
            ),
        ],
    )

    print(f"\nPlan: {plan.goal}")
    print(f"Steps: {len(plan.steps)}")

    # Create orchestrator and execute
    orchestrator = Orchestrator(registry=registry, parallel=True)

    print("\nExecuting plan...")
    result_plan = orchestrator.execute(plan)

    # Show results
    print("\n--- Results ---")
    for step in result_plan.steps:
        status_icon = "✓" if step.status == StepStatus.COMPLETED else "✗"
        print(f"{status_icon} {step.id}: {step.status.value}")
        if step.output:
            print(f"   Output: {step.output[:60]}...")

    # Count successes
    completed = sum(1 for s in result_plan.steps if s.status == StepStatus.COMPLETED)
    print(f"\n{completed}/{len(result_plan.steps)} steps completed")


if __name__ == "__main__":
    main()
