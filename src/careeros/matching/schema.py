from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class MatchResult(BaseModel):
    version: str = "v1"

    run_id: str
    profile_path: str
    job_path: str

    overlap_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)

    score: float = 0.0              # 0–100
    rationale: List[str] = Field(default_factory=list)

    evidence_map: Dict[str, str] = Field(default_factory=dict)  # skill -> "resume" | "missing"
