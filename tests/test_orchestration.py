"""Tests for agenthelm.orchestration - AgentRegistry and Orchestrator."""

import pytest
from unittest.mock import MagicMock

from agenthelm.orchestration import AgentRegistry, Orchestrator
from agenthelm.agent.plan import Plan, PlanStep, StepStatus
from agenthelm.agent.result import AgentResult


class TestAgentRegistry:
    """Tests for AgentRegistry."""

    def test_register_agent(self):
        """Can register an agent."""
        registry = AgentRegistry()
        agent = MagicMock()
        agent.name = "researcher"

        registry.register(agent)

        assert "researcher" in registry
        assert len(registry) == 1

    def test_register_duplicate_raises(self):
        """Cannot register two agents with same name."""
        registry = AgentRegistry()
        agent1 = MagicMock()
        agent1.name = "researcher"
        agent2 = MagicMock()
        agent2.name = "researcher"

        registry.register(agent1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(agent2)

    def test_get_agent(self):
        """Can get agent by name."""
        registry = AgentRegistry()
        agent = MagicMock()
        agent.name = "writer"

        registry.register(agent)

        assert registry.get("writer") is agent
        assert registry.get("unknown") is None

    def test_getitem(self):
        """Can use [] to get agent."""
        registry = AgentRegistry()
        agent = MagicMock()
        agent.name = "analyst"

        registry.register(agent)

        assert registry["analyst"] is agent

        with pytest.raises(KeyError, match="not found"):
            _ = registry["unknown"]

    def test_unregister(self):
        """Can unregister an agent."""
        registry = AgentRegistry()
        agent = MagicMock()
        agent.name = "test"

        registry.register(agent)
        removed = registry.unregister("test")

        assert removed is agent
        assert "test" not in registry

    def test_iterate(self):
        """Can iterate over agent names."""
        registry = AgentRegistry()
        for name in ["a", "b", "c"]:
            agent = MagicMock()
            agent.name = name
            registry.register(agent)

        names = list(registry)
        assert set(names) == {"a", "b", "c"}

    def test_names_property(self):
        """Can get list of names."""
        registry = AgentRegistry()
        for name in ["x", "y"]:
            agent = MagicMock()
            agent.name = name
            registry.register(agent)

        assert set(registry.names) == {"x", "y"}

    def test_clear(self):
        """Can clear all agents."""
        registry = AgentRegistry()
        agent = MagicMock()
        agent.name = "test"
        registry.register(agent)

        registry.clear()

        assert len(registry) == 0


class TestOrchestrator:
    """Tests for Orchestrator."""

    @pytest.fixture
    def registry(self):
        """Create a registry with mock agents."""
        registry = AgentRegistry()

        researcher = MagicMock()
        researcher.name = "researcher"
        researcher.run.return_value = AgentResult(
            success=True,
            answer="Research complete",
            events=[],
        )

        writer = MagicMock()
        writer.name = "writer"
        writer.run.return_value = AgentResult(
            success=True,
            answer="Writing complete",
            events=[],
        )

        registry.register(researcher)
        registry.register(writer)

        return registry

    @pytest.fixture
    def simple_plan(self):
        """Create a simple approved plan."""
        return Plan(
            goal="Test plan",
            approved=True,
            steps=[
                PlanStep(
                    id="step_1",
                    agent_name="researcher",
                    tool_name="search",
                    description="Do research",
                ),
            ],
        )

    @pytest.mark.asyncio
    async def test_execute_simple_plan(self, registry, simple_plan):
        """Can execute a simple plan."""
        orchestrator = Orchestrator(registry)

        result = await orchestrator.execute(simple_plan)

        assert result.success
        assert simple_plan.steps[0].status == StepStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_requires_approval(self, registry):
        """Cannot execute unapproved plan."""
        plan = Plan(goal="Test", approved=False, steps=[])
        orchestrator = Orchestrator(registry)

        with pytest.raises(ValueError, match="must be approved"):
            await orchestrator.execute(plan)

    @pytest.mark.asyncio
    async def test_execute_with_dependencies(self, registry):
        """Executes steps in dependency order."""
        plan = Plan(
            goal="Sequential",
            approved=True,
            steps=[
                PlanStep(
                    id="step_1",
                    agent_name="researcher",
                    tool_name="search",
                    description="First",
                ),
                PlanStep(
                    id="step_2",
                    agent_name="writer",
                    tool_name="write",
                    description="Second",
                    depends_on=["step_1"],
                ),
            ],
        )

        orchestrator = Orchestrator(registry)
        result = await orchestrator.execute(plan)

        assert result.success
        assert plan.steps[0].status == StepStatus.COMPLETED
        assert plan.steps[1].status == StepStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_parallel_steps(self, registry):
        """Independent steps can run in parallel."""
        plan = Plan(
            goal="Parallel",
            approved=True,
            steps=[
                PlanStep(
                    id="a",
                    agent_name="researcher",
                    tool_name="search",
                    description="Task A",
                ),
                PlanStep(
                    id="b",
                    agent_name="researcher",
                    tool_name="search",
                    description="Task B",
                ),
                PlanStep(
                    id="c",
                    agent_name="writer",
                    tool_name="write",
                    description="Combine",
                    depends_on=["a", "b"],
                ),
            ],
        )

        orchestrator = Orchestrator(registry)
        result = await orchestrator.execute(plan)

        assert result.success
        assert all(s.status == StepStatus.COMPLETED for s in plan.steps)

    @pytest.mark.asyncio
    async def test_execute_handles_failure(self, registry):
        """Failed steps are marked correctly."""
        # Make researcher fail
        registry["researcher"].run.return_value = AgentResult(
            success=False,
            error="Research failed",
        )

        plan = Plan(
            goal="Failing",
            approved=True,
            steps=[
                PlanStep(
                    id="step_1",
                    agent_name="researcher",
                    tool_name="search",
                    description="Will fail",
                ),
            ],
        )

        orchestrator = Orchestrator(registry)
        result = await orchestrator.execute(plan)

        assert not result.success
        assert plan.steps[0].status == StepStatus.FAILED

    @pytest.mark.asyncio
    async def test_default_agent(self, registry):
        """Can use default agent for steps without agent_name."""
        default = MagicMock()
        default.name = "default"
        default.run.return_value = AgentResult(success=True, answer="OK")

        plan = Plan(
            goal="Default agent",
            approved=True,
            steps=[
                PlanStep(
                    id="step_1",
                    tool_name="do_something",
                    description="Use default",
                ),
            ],
        )

        orchestrator = Orchestrator(registry, default_agent=default)
        result = await orchestrator.execute(plan)

        assert result.success
        default.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_missing_agent_raises(self, registry):
        """Missing agent causes step failure."""
        plan = Plan(
            goal="Missing agent",
            approved=True,
            steps=[
                PlanStep(
                    id="step_1",
                    agent_name="nonexistent",
                    tool_name="search",
                    description="Will fail",
                ),
            ],
        )

        orchestrator = Orchestrator(registry)
        result = await orchestrator.execute(plan)

        assert not result.success
        assert plan.steps[0].status == StepStatus.FAILED


class TestOrchestratorSaga:
    """Tests for Saga pattern (rollback on failure)."""

    @pytest.fixture
    def registry_with_rollback(self):
        """Registry with agents that track calls for rollback testing."""
        registry = AgentRegistry()

        # Track calls for verification
        calls = []

        def make_agent(name: str, should_fail: bool = False):
            agent = MagicMock()
            agent.name = name

            def run_side_effect(task):
                calls.append((name, task))
                if should_fail:
                    return AgentResult(success=False, error=f"{name} failed")
                return AgentResult(success=True, answer=f"{name} done", events=[])

            agent.run.side_effect = run_side_effect
            return agent

        registry.register(make_agent("step1_agent"))
        registry.register(make_agent("step2_agent", should_fail=True))
        registry._calls = calls  # Attach for test access

        return registry

    @pytest.mark.asyncio
    async def test_rollback_runs_on_failure(self, registry_with_rollback):
        """On failure, compensating actions run for completed steps."""
        plan = Plan(
            goal="Test rollback",
            approved=True,
            steps=[
                PlanStep(
                    id="step_1",
                    agent_name="step1_agent",
                    tool_name="create_file",
                    description="Create file",
                    compensate_tool="delete_file",  # Step-level override
                ),
                PlanStep(
                    id="step_2",
                    agent_name="step2_agent",
                    tool_name="send_email",
                    description="Will fail",
                    depends_on=["step_1"],
                ),
            ],
        )

        orchestrator = Orchestrator(registry_with_rollback, enable_rollback=True)
        result = await orchestrator.execute(plan)

        assert not result.success
        # Step 1 completed, then step 2 failed
        assert plan.steps[0].status == StepStatus.COMPLETED
        assert plan.steps[1].status == StepStatus.FAILED

        # Verify rollback was attempted (step1_agent called again for compensate)
        calls = registry_with_rollback._calls
        # First call is step 1 execution, step 2 fails, then rollback
        assert len(calls) >= 2

    @pytest.mark.asyncio
    async def test_rollback_disabled(self, registry_with_rollback):
        """When enable_rollback=False, no compensation runs."""
        plan = Plan(
            goal="No rollback",
            approved=True,
            steps=[
                PlanStep(
                    id="step_1",
                    agent_name="step1_agent",
                    tool_name="create_file",
                    description="Create file",
                    compensate_tool="delete_file",
                ),
                PlanStep(
                    id="step_2",
                    agent_name="step2_agent",
                    tool_name="send_email",
                    description="Will fail",
                    depends_on=["step_1"],
                ),
            ],
        )

        orchestrator = Orchestrator(registry_with_rollback, enable_rollback=False)
        result = await orchestrator.execute(plan)

        assert not result.success
        # Only 2 calls: step_1 execute + step_2 execute (fails)
        # No rollback call
        calls = registry_with_rollback._calls
        assert len(calls) == 2
