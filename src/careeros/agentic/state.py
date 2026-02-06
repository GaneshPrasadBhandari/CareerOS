from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field

StepStatus = Literal["pending", "running", "ok", "blocked", "error", "skipped"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StepTrace(BaseModel):
    step_id: str
    tool_name: str
    status: StepStatus = "pending"
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    input_ref: dict[str, Any] = Field(default_factory=dict)   # metadata only (paths, ids)
    output_ref: dict[str, Any] = Field(default_factory=dict)  # metadata only (paths, ids)
    message: Optional[str] = None


class ApprovalDecision(BaseModel):
    tool_name: str
    approved: bool
    decided_by: str = "human"
    decided_at: datetime = Field(default_factory=utc_now)
    reason: Optional[str] = None


class ArtifactIndex(BaseModel):
    intake_path: Optional[str] = None
    profile_path: Optional[str] = None
    job_paths: list[str] = Field(default_factory=list)
    match_paths: list[str] = Field(default_factory=list)
    shortlist_path: Optional[str] = None
    package_path: Optional[str] = None
    validation_report_path: Optional[str] = None
    export_dir: Optional[str] = None
    tracking_ledger_path: Optional[str] = None
    followups_path: Optional[str] = None
    drafts_path: Optional[str] = None


class OrchestratorState(BaseModel):
    run_id: str
    env: str = "dev"
    orchestration_mode: str = "deterministic"
    created_at: datetime = Field(default_factory=utc_now)

    artifacts: ArtifactIndex = Field(default_factory=ArtifactIndex)
    steps: list[StepTrace] = Field(default_factory=list)
    approvals: list[ApprovalDecision] = Field(default_factory=list)

    def start_step(self, step_id: str, tool_name: str, input_ref: dict[str, Any] | None = None) -> None:
        self.steps.append(
            StepTrace(
                step_id=step_id,
                tool_name=tool_name,
                status="running",
                started_at=utc_now(),
                input_ref=input_ref or {},
            )
        )

    def end_step(
        self,
        step_id: str,
        status: StepStatus,
        output_ref: dict[str, Any] | None = None,
        message: str | None = None,
    ) -> None:
        for s in reversed(self.steps):
            if s.step_id == step_id:
                s.status = status
                s.ended_at = utc_now()
                s.output_ref = output_ref or {}
                s.message = message
                return
        raise ValueError(f"Step not found: {step_id}")

    def is_approved(self, tool_name: str) -> bool:
        for d in reversed(self.approvals):
            if d.tool_name == tool_name:
                return d.approved
        return False

    def record_approval(self, tool_name: str, approved: bool, reason: str | None = None) -> None:
        self.approvals.append(
            ApprovalDecision(tool_name=tool_name, approved=approved, reason=reason)
        )
