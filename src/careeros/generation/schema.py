from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class ResumeBullet(BaseModel):
    text: str
    evidence_skills: List[str] = Field(default_factory=list)
    evidence_chunk_ids: List[str] = Field(default_factory=list)

class CoverLetterDraft(BaseModel):
    subject: str
    paragraphs: List[str] = Field(default_factory=list)


class ApplicationPackage(BaseModel):
    version: str = "v1"

    run_id: str
    profile_path: str
    job_path: str

    job_title_hint: Optional[str] = None
    company_hint: Optional[str] = None

    bullets: List[ResumeBullet] = Field(default_factory=list)
    cover_letter: CoverLetterDraft
    qa_stubs: Dict[str, str] = Field(default_factory=dict)  # q -> draft answer



class ApplicationPackageV2(BaseModel):
    """P17 grounded package where each generated claim must be evidence-backed."""

    version: str = "v2"

    run_id: str
    profile_path: str
    job_path: str

    job_title_hint: Optional[str] = None
    company_hint: Optional[str] = None

    bullets: List[ResumeBullet] = Field(default_factory=list)
    cover_letter: CoverLetterDraft
    qa_stubs: Dict[str, str] = Field(default_factory=dict)

    citations_required: bool = True
    citations_complete: bool = False