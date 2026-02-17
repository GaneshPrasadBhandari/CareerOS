from __future__ import annotations

from careeros.matching.service import compute_match
from careeros.parsing.schema import EvidenceProfile
from careeros.jobs.schema import JobPost


def run(profile: EvidenceProfile, job: JobPost, *, run_id: str, profile_path: str, job_path: str):
    return compute_match(profile, job, run_id=run_id, profile_path=profile_path, job_path=job_path)
