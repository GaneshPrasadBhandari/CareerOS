"""P20 contract models for Phase 3 agentic orchestration.

These schemas define the minimal typed interface between:
- Planner/orchestrator (L3)
- Agent workers (L4)
- Artifact and validation layer (L6/L9)

Goal:
Keep every agent call explicit, testable, and serializable before enabling live LLM/tool calls.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AgentTaskInput(BaseModel):
    """Validated input contract for one agent task.

    Attributes:
        run_id: Global run identifier to correlate artifacts and logs.
        agent: Logical agent role executing the task.
        objective: Human-readable purpose of this step.
        profile_path: Optional profile artifact path.
        job_path: Optional job artifact path.
        constraints: Optional policy/runtime constraints.
    """

    run_id: str
    agent: Literal["planner", "matcher", "generator", "guardrails", "notifier"]
    objective: str = Field(min_length=3)
    profile_path: str | None = None
    job_path: str | None = None
    constraints: dict = Field(default_factory=dict)


class AgentTaskOutput(BaseModel):
    """Standardized output envelope returned by an agent step."""

    run_id: str
    agent: str
    status: Literal["ok", "blocked", "error"]
    artifact_paths: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ContractValidationResult(BaseModel):
    """Result of schema validation for Phase 3 contracts."""

    status: Literal["ok", "error"]
    errors: list[str] = Field(default_factory=list)
    normalized: dict = Field(default_factory=dict)
