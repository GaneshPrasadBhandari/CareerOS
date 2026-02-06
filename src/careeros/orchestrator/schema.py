from __future__ import annotations

from typing import Optional, Dict, Any, Literal, List
from pydantic import BaseModel


StepStatus = Literal["ok", "skipped", "blocked", "error"]


class StepResult(BaseModel):
    name: str
    status: StepStatus
    artifact_path: Optional[str] = None
    detail: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class OrchestrationRun(BaseModel):
    version: str = "v1"
    run_id: str
    status: Literal["ok", "blocked", "error"]
    steps: List[StepResult]
    outputs: Dict[str, Optional[str]]  # package, report, docx, pdf, followups, drafts
