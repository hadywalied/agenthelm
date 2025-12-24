"""Plan and PlanStep models for structured agent planning."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class StepStatus(str, Enum):
    """Status of a plan step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanStep(BaseModel):
    """
    A single step in an execution plan.

    Steps can have dependencies for parallel/sequential execution.
    Supports Saga pattern with compensating actions on failure.
    """

    id: str = Field(description="Unique step identifier")
    agent_name: str | None = Field(default=None, description="Agent to delegate to")
    tool_name: str = Field(description="Name of the tool to execute")
    description: str = Field(description="Human-readable description of this step")
    args: dict[str, Any] = Field(
        default_factory=dict, description="Arguments to pass to the tool"
    )
    depends_on: list[str] = Field(
        default_factory=list, description="IDs of steps that must complete first"
    )

    # Saga pattern: compensating action (overrides tool-level default)
    compensate_tool: str | None = Field(
        default=None, description="Tool to run on rollback (overrides tool default)"
    )
    compensate_args: dict[str, Any] = Field(
        default_factory=dict, description="Arguments for compensating tool"
    )

    # Runtime state
    status: StepStatus = Field(default=StepStatus.PENDING, description="Current status")
    result: Any | None = Field(default=None, description="Result after execution")
    error: str | None = Field(default=None, description="Error if failed")

    @property
    def is_ready(self) -> bool:
        """Check if step is ready to execute (no pending dependencies)."""
        return self.status == StepStatus.PENDING and len(self.depends_on) == 0


class Plan(BaseModel):
    """
    A structured execution plan with potentially parallel steps.

    Steps with no dependencies can run in parallel.
    Steps with dependencies run after their dependencies complete.
    """

    goal: str = Field(description="The goal this plan aims to achieve")
    steps: list[PlanStep] = Field(default_factory=list, description="Ordered steps")
    reasoning: str = Field(default="", description="LLM reasoning for this plan")

    # Execution state
    approved: bool = Field(
        default=False, description="Whether plan has been approved for execution"
    )

    def get_ready_steps(self) -> list[PlanStep]:
        """Get all steps that are ready to execute (no pending dependencies)."""
        completed_ids = {s.id for s in self.steps if s.status == StepStatus.COMPLETED}

        ready = []
        for step in self.steps:
            if step.status != StepStatus.PENDING:
                continue
            # Check if all dependencies are completed
            if all(dep_id in completed_ids for dep_id in step.depends_on):
                ready.append(step)
        return ready

    def get_step(self, step_id: str) -> PlanStep | None:
        """Get a step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def mark_completed(self, step_id: str, result: Any = None) -> None:
        """Mark a step as completed."""
        step = self.get_step(step_id)
        if step:
            step.status = StepStatus.COMPLETED
            step.result = result

    def mark_failed(self, step_id: str, error: str) -> None:
        """Mark a step as failed."""
        step = self.get_step(step_id)
        if step:
            step.status = StepStatus.FAILED
            step.error = error

    @property
    def is_complete(self) -> bool:
        """Check if all steps are completed or failed."""
        return all(
            s.status in (StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED)
            for s in self.steps
        )

    @property
    def success(self) -> bool:
        """Check if plan completed successfully (all steps completed)."""
        return all(s.status == StepStatus.COMPLETED for s in self.steps)

    def to_yaml(self) -> str:
        """Serialize plan to YAML for human review."""
        import yaml

        data = {
            "goal": self.goal,
            "reasoning": self.reasoning,
            "steps": [
                {
                    "id": s.id,
                    "agent": s.agent_name,
                    "tool": s.tool_name,
                    "description": s.description,
                    "args": s.args,
                    "depends_on": s.depends_on if s.depends_on else None,
                }
                for s in self.steps
            ],
        }
        # Filter None values
        for step in data["steps"]:
            step = {k: v for k, v in step.items() if v is not None}
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
