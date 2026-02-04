from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional


class JobPost(BaseModel):
    version: str = "v1"
    source: str = "paste"        # later: "url"
    url: Optional[str] = None

    company: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None
    remote: Optional[bool] = None

    raw_text: str

    keywords: List[str] = Field(default_factory=list)
