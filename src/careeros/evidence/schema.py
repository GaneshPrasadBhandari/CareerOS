from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List


class EvidenceChunk(BaseModel):
    chunk_id: str
    source: str = "profile"
    text: str
    tags: List[str] = Field(default_factory=list)


class EvidenceRetrievalResult(BaseModel):
    query: str
    chunks: List[EvidenceChunk] = Field(default_factory=list)
