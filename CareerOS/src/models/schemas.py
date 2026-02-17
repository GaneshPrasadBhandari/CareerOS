from typing import List, Optional
from pydantic import BaseModel, Field

class Education(BaseModel):
    """Schema for degree and university details."""
    degree: str = Field(..., description="E.g., Bachelor of Science")
    university: str = Field(..., description="Full institution name")
    major: str = Field(..., description="Field of study")
    graduation_year: Optional[int] = None

class Experience(BaseModel):
    """Schema for job history."""
    job_title: str
    company: str
    duration: str
    key_achievements: List[str] = Field(default_factory=list)

class ResumeSchema(BaseModel):
    """The master contract for our Parser Agent."""
    full_name: str
    email: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    work_history: List[Experience] = Field(default_factory=list)
    summary: Optional[str] = Field(None, description="2-3 sentence bio")