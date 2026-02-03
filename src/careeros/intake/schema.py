from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class Constraints(BaseModel):
    location: Optional[str] = None
    remote_only: bool = False
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    work_auth: Optional[str] = None  # e.g., F1/CPT/OPT/H1B
    relocation_ok: bool = False


class Links(BaseModel):
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None


class IntakeBundle(BaseModel):
    version: str = "v1"
    candidate_name: Optional[str] = None

    target_roles: List[str] = Field(default_factory=list)
    target_industries: List[str] = Field(default_factory=list)

    constraints: Constraints = Field(default_factory=Constraints)
    links: Links = Field(default_factory=Links)

    notes: Optional[str] = None
