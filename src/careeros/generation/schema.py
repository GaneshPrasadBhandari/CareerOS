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




class TailoredResume(BaseModel):
    headline: str = ""
    professional_summary: str = ""
    core_skills: List[str] = Field(default_factory=list)
    experience_highlights: List[str] = Field(default_factory=list)
    projects_highlights: List[str] = Field(default_factory=list)

class ApplicationPackage(BaseModel):
    version: str = "v1"

    run_id: str
    profile_path: str
    job_path: str

    job_title_hint: Optional[str] = None
    company_hint: Optional[str] = None

    bullets: List[ResumeBullet] = Field(default_factory=list)
    tailored_resume: TailoredResume = Field(default_factory=TailoredResume)
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
    tailored_resume: TailoredResume = Field(default_factory=TailoredResume)
    cover_letter: CoverLetterDraft
    qa_stubs: Dict[str, str] = Field(default_factory=dict)

    citations_required: bool = True
    citations_complete: bool = False