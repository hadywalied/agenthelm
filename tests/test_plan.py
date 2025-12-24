"""Tests for agenthelm.agent - Plan and PlanStep models."""

import pytest

from agenthelm.agent.plan import Plan, PlanStep, StepStatus


class TestPlanStep:
    """Tests for PlanStep model."""

    def test_create_basic_step(self):
        """Create a basic plan step."""
        step = PlanStep(
            id="step_1",
            tool_name="get_weather",
            description="Get weather for NYC",
            args={"city": "New York"},
        )
        assert step.id == "step_1"
        assert step.tool_name == "get_weather"
        assert step.status == StepStatus.PENDING
        assert step.agent_name is None

    def test_step_with_agent(self):
        """Step can have an agent assignment."""
        step = PlanStep(
            id="step_1",
            agent_name="researcher",
            tool_name="search",
            description="Search for info",
        )
        assert step.agent_name == "researcher"

    def test_step_with_dependencies(self):
        """Step can have dependencies."""
        step = PlanStep(
            id="step_2",
            tool_name="summarize",
            description="Summarize results",
            depends_on=["step_1"],
        )
        assert step.depends_on == ["step_1"]
        assert not step.is_ready  # Has dependencies

    def test_step_is_ready(self):
        """Step with no dependencies is ready."""
        step = PlanStep(
            id="step_1",
            tool_name="search",
            description="Search",
        )
        assert step.is_ready


class TestPlan:
    """Tests for Plan model."""

    @pytest.fixture
    def sample_plan(self):
        """Create a sample plan with steps."""
        return Plan(
            goal="Research and summarize topic",
            reasoning="First search, then summarize",
            steps=[
                PlanStep(
                    id="step_1",
                    tool_name="search",
                    description="Search for info",
                ),
                PlanStep(
                    id="step_2",
                    tool_name="summarize",
                    description="Summarize results",
                    depends_on=["step_1"],
                ),
            ],
        )

    def test_create_plan(self, sample_plan):
        """Create a basic plan."""
        assert sample_plan.goal == "Research and summarize topic"
        assert len(sample_plan.steps) == 2
        assert not sample_plan.approved

    def test_get_ready_steps(self, sample_plan):
        """Get steps that are ready to execute."""
        ready = sample_plan.get_ready_steps()
        assert len(ready) == 1
        assert ready[0].id == "step_1"

    def test_get_ready_steps_after_completion(self, sample_plan):
        """After step_1 completes, step_2 becomes ready."""
        sample_plan.mark_completed("step_1", result="search results")

        ready = sample_plan.get_ready_steps()
        assert len(ready) == 1
        assert ready[0].id == "step_2"

    def test_mark_completed(self, sample_plan):
        """Mark a step as completed."""
        sample_plan.mark_completed("step_1", result="done")

        step = sample_plan.get_step("step_1")
        assert step.status == StepStatus.COMPLETED
        assert step.result == "done"

    def test_mark_failed(self, sample_plan):
        """Mark a step as failed."""
        sample_plan.mark_failed("step_1", error="Connection error")

        step = sample_plan.get_step("step_1")
        assert step.status == StepStatus.FAILED
        assert step.error == "Connection error"

    def test_is_complete(self, sample_plan):
        """Check if plan is complete."""
        assert not sample_plan.is_complete

        sample_plan.mark_completed("step_1")
        assert not sample_plan.is_complete

        sample_plan.mark_completed("step_2")
        assert sample_plan.is_complete

    def test_success(self, sample_plan):
        """Check if plan succeeded."""
        sample_plan.mark_completed("step_1")
        sample_plan.mark_failed("step_2", "error")

        assert sample_plan.is_complete
        assert not sample_plan.success

    def test_to_yaml(self, sample_plan):
        """Serialize plan to YAML."""
        yaml_output = sample_plan.to_yaml()

        assert "goal:" in yaml_output
        assert "Research and summarize topic" in yaml_output
        assert "step_1" in yaml_output
        assert "search" in yaml_output

    def test_parallel_steps(self):
        """Steps without dependencies can run in parallel."""
        plan = Plan(
            goal="Parallel task",
            steps=[
                PlanStep(id="a", tool_name="task_a", description="A"),
                PlanStep(id="b", tool_name="task_b", description="B"),
                PlanStep(
                    id="c", tool_name="task_c", description="C", depends_on=["a", "b"]
                ),
            ],
        )

        ready = plan.get_ready_steps()
        assert len(ready) == 2
        assert {s.id for s in ready} == {"a", "b"}

        plan.mark_completed("a")
        ready = plan.get_ready_steps()
        assert len(ready) == 1
        assert ready[0].id == "b"

        plan.mark_completed("b")
        ready = plan.get_ready_steps()
        assert len(ready) == 1
        assert ready[0].id == "c"
