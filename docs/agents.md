# Agents

AgentHelm provides DSPy-native agents for tool calling and planning.

## Quick Start

```python
import dspy
from agenthelm import ToolAgent, PlannerAgent

# Configure your LLM
lm = dspy.LM("mistral/mistral-large-latest")

# Create a tool agent
agent = ToolAgent(
    name="assistant",
    lm=lm,
    tools=[my_search_tool, my_summarize_tool],
    max_iters=10
)
result = agent.run("What is the weather in NYC?")
print(result.answer)

# Create a planner agent
planner = PlannerAgent(
    name="planner",
    lm=lm,
    tools=[search, summarize, write_file]
)
plan = planner.plan("Research AI trends and create a report")
print(plan.to_yaml())  # Review before execution
```

## Agent Types

### ToolAgent

ReAct-style agent that reasons and executes tools in a loop.

```python
from agenthelm import ToolAgent, tool

@tool()
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Sunny in {city}"

agent = ToolAgent(name="weather_bot", lm=lm, tools=[get_weather])
result = agent.run("What's the weather in Paris?")

# Access results
print(result.success)    # True
print(result.answer)     # "The weather in Paris is sunny."
print(result.events)     # List of traced tool executions
```

### PlannerAgent

Generates structured execution plans before acting.

```python
from agenthelm import PlannerAgent

planner = PlannerAgent(name="planner", lm=lm, tools=[search, analyze, report])
plan = planner.plan("Analyze competitor pricing")

# Review the plan
print(plan.goal)       # "Analyze competitor pricing strategies"
print(plan.reasoning)  # LLM's reasoning
for step in plan.steps:
    print(f"  {step.id}: {step.tool_name} - {step.description}")

# Execution is handled by Orchestrator (Week 4)
```

## AgentResult

All agents return an `AgentResult` with execution details:

```python
result = agent.run("Do something")

result.success          # bool - Did the agent complete successfully?
result.answer           # str | None - Final answer
result.error            # str | None - Error message if failed
result.events           # list[Event] - All traced tool executions
result.total_cost_usd   # float - Aggregated LLM cost
result.token_usage      # TokenUsage - Aggregated tokens
result.iterations       # int - Number of reasoning loops
```

## Plan Schema

Plans are structured for parallel and sequential execution:

```python
from agenthelm import Plan, PlanStep, StepStatus

plan = Plan(
    goal="Research and summarize",
    steps=[
        PlanStep(id="1", tool_name="search", description="Find sources"),
        PlanStep(id="2", tool_name="search", description="Find more sources"),
        PlanStep(id="3", tool_name="summarize", description="Combine results",
                 depends_on=["1", "2"]),  # Runs after 1 and 2 complete
    ]
)

# Steps 1 and 2 can run in parallel (no dependencies)
ready = plan.get_ready_steps()  # Returns steps 1 and 2

# After completion
plan.mark_completed("1", result="source A")
plan.mark_completed("2", result="source B")

# Now step 3 is ready
ready = plan.get_ready_steps()  # Returns step 3
```

## Memory Integration

Agents can use the Memory Hub for context persistence:

```python
from agenthelm import ToolAgent, MemoryHub

hub = MemoryHub(data_dir="./data")

agent = ToolAgent(
    name="memory_agent",
    lm=lm,
    tools=[search],
    memory=hub
)

# Agent can use memory internally
# await agent._remember("User prefers dark mode")
# results = await agent._recall("user preferences")
```

## Tracing Integration

Agents automatically trace tool executions when given a tracer:

```python
from agenthelm import ToolAgent, ExecutionTracer
from agenthelm.core.storage import SqliteStorage

tracer = ExecutionTracer(storage=SqliteStorage("traces.db"))

agent = ToolAgent(
    name="traced_agent",
    lm=lm,
    tools=[my_tool],
    tracer=tracer
)

result = agent.run("Do something")
# All tool calls are now persisted to traces.db
```

## API Reference

::: agenthelm.BaseAgent
options:
show_source: false

::: agenthelm.ToolAgent
options:
show_source: false

::: agenthelm.PlannerAgent
options:
show_source: false

::: agenthelm.AgentResult
options:
show_source: false

::: agenthelm.Plan
options:
show_source: false

::: agenthelm.PlanStep
options:
show_source: false
