from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional


class ExperienceItem(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    highlights: List[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    name: Optional[str] = None
    stack: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)
    link: Optional[str] = None


class EvidenceProfile(BaseModel):
    version: str = "v1"
    candidate_name: Optional[str] = None

    raw_text: str
    skills: List[str] = Field(default_factory=list)
    titles: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)

    experiences: List[ExperienceItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
