from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class StepTrace(BaseModel):
    step_id: str
    status: str = "running"

    # ✅ tests pass dict sometimes
    message: Any = ""

    started_at_utc: str = Field(default_factory=lambda: _iso(_utc_now()))
    finished_at_utc: Optional[str] = None

    # ✅ tests sometimes pass "tool.a" (string) not dict
    input_ref: Any = Field(default_factory=dict)

    # output can be dict or string (we normalize)
    output_ref: Dict[str, Any] = Field(default_factory=dict)

    # convenience mirror (some code uses outputs)
    outputs: Dict[str, Any] = Field(default_factory=dict)


class ApprovalDecision(BaseModel):
    tool_name: str
    approved: bool
    reason: Optional[str] = None
    decided_at_utc: str = Field(default_factory=lambda: _iso(_utc_now()))


class ArtifactIndex(BaseModel):
    profile_path: Optional[str] = None
    job_path: Optional[str] = None
    shortlist_path: Optional[str] = None

    package_path: Optional[str] = None
    validation_report_path: Optional[str] = None

    export_docx_path: Optional[str] = None
    export_pdf_path: Optional[str] = None

    tracking_path: Optional[str] = None
    application_id: Optional[str] = None

    followups_path: Optional[str] = None
    drafts_path: Optional[str] = None

    overlap_skills: List[str] = Field(default_factory=list)


class OrchestratorState(BaseModel):
    version: str = "v1"
    run_id: str
    created_at_utc: str = Field(default_factory=lambda: _iso(_utc_now()))
    updated_at_utc: str = Field(default_factory=lambda: _iso(_utc_now()))

    mode: str = "deterministic"
    env: Optional[str] = None

    artifacts: ArtifactIndex = Field(default_factory=ArtifactIndex)
    steps: List[StepTrace] = Field(default_factory=list)
    approvals: List[ApprovalDecision] = Field(default_factory=list)

    @classmethod
    def new(cls, run_id: Optional[str] = None, *, mode: str = "deterministic", env: Optional[str] = None) -> "OrchestratorState":
        rid = run_id or uuid.uuid4().hex
        return cls(run_id=rid, mode=mode, env=env)

    def start_step(self, step_id: str, tool_name: str = "", input_ref: Any = None) -> StepTrace:
        """
        Test contract:
        start_step(step_id, tool_name, input_ref_dict)
        Example:
        start_step("s1", "tool.a", {"input_path":"a.json"})
        """
        s = StepTrace(step_id=step_id, status="running", message="")
        if tool_name:
            # store tool name inside input_ref for traceability
            s.input_ref = {"tool_name": tool_name}
        else:
            s.input_ref = {}

        if input_ref is not None:
            if isinstance(input_ref, dict):
                s.input_ref.update(input_ref)
            else:
                # if someone passes a string/path etc
                s.input_ref["input"] = input_ref
        self.steps.append(s)
        self.updated_at_utc = _iso(_utc_now())
        return s


    def end_step(
    self,
    step_id: str,
    status: str = "ok",
    output_ref: Any = None,
    message: Any = "",
    outputs: Optional[Any] = None,
    output_path: Optional[str] = None,
    ) -> StepTrace:

        target: Optional[StepTrace] = None
        for s in reversed(self.steps):
            if s.step_id == step_id:
                target = s
                break
        if target is None:
            target = self.start_step(step_id)

        out: Any = outputs if outputs is not None else (output_ref or {})

        # normalize to dict
        if isinstance(out, str):
            out = {"output_path": out}
        if not isinstance(out, dict):
            out = {"value": out}

        if output_path:
            out["output_path"] = str(output_path)

        # useful fallbacks
        if "path" in out and "output_path" not in out:
            out["output_path"] = out["path"]
        if "artifact_path" in out and "output_path" not in out:
            out["output_path"] = out["artifact_path"]

        target.status = status
        target.message = message
        target.finished_at_utc = _iso(_utc_now())
        target.output_ref = dict(out)
        target.outputs = dict(out)

        self.updated_at_utc = _iso(_utc_now())
        return target

    def record_approval(self, tool_name: str, approved: bool, reason: Optional[str] = None) -> ApprovalDecision:
        d = ApprovalDecision(tool_name=tool_name, approved=approved, reason=reason)
        self.approvals.append(d)
        self.updated_at_utc = _iso(_utc_now())
        return d

    def is_approved(self, tool_name: str) -> bool:
        for d in reversed(self.approvals):
            if d.tool_name == tool_name:
                return bool(d.approved)
        return False
