"""
AgentHelm Agent Module - DSPy-native agents with tool calling and planning.

Example usage:
    from agenthelm.agent import ToolAgent, PlannerAgent, AgentResult

    # Create a tool agent
    agent = ToolAgent(name="assistant", lm=my_lm, tools=[my_tool])
    result = agent.run("What is the weather?")

    # Create a planner agent
    planner = PlannerAgent(name="planner", lm=my_lm, tools=[search, summarize])
    plan = planner.plan("Research this topic")
"""

from agenthelm.agent.base import BaseAgent
from agenthelm.agent.result import AgentResult
from agenthelm.agent.plan import Plan, PlanStep, StepStatus
from agenthelm.agent.tool_agent import ToolAgent
from agenthelm.agent.planner import PlannerAgent

__all__ = [
    # Base
    "BaseAgent",
    "AgentResult",
    # Planning
    "Plan",
    "PlanStep",
    "StepStatus",
    # Agents
    "ToolAgent",
    "PlannerAgent",
]
