from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict


class RankedItem(BaseModel):
    job_path: str
    score: float
    overlap_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)


class RankedShortlist(BaseModel):
    version: str = "v1"
    run_id: str
    profile_path: str
    items: List[RankedItem] = Field(default_factory=list)
    top_n: int = 3
