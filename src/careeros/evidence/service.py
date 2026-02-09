from __future__ import annotations

import re
from typing import List

from careeros.parsing.schema import EvidenceProfile
from careeros.evidence.schema import EvidenceChunk, EvidenceRetrievalResult


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "unknown"


def build_profile_skill_chunks(profile: EvidenceProfile) -> List[EvidenceChunk]:
    chunks: List[EvidenceChunk] = []
    for i, skill in enumerate(profile.skills, start=1):
        sid = _slug(skill)
        chunks.append(
            EvidenceChunk(
                chunk_id=f"profile_skill_{i}_{sid}",
                source="profile.skills",
                text=f"Candidate evidence includes skill: {skill}",
                tags=[skill.lower()],
            )
        )
    return chunks


def retrieve_chunks_for_skills(profile: EvidenceProfile, required_skills: List[str]) -> EvidenceRetrievalResult:
    chunks = build_profile_skill_chunks(profile)
    required = {s.lower() for s in required_skills}
    matched = [c for c in chunks if required.intersection(set(c.tags))]
    return EvidenceRetrievalResult(query=", ".join(required_skills), chunks=matched)
