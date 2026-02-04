from __future__ import annotations

from pathlib import Path
from datetime import datetime

from careeros.parsing.schema import EvidenceProfile
from careeros.jobs.schema import JobPost
from careeros.matching.schema import MatchResult


def compute_match(profile: EvidenceProfile, job: JobPost, run_id: str, profile_path: str, job_path: str) -> MatchResult:
    pskills = set([s.lower() for s in profile.skills])
    jskills = set([k.lower() for k in job.keywords])

    overlap = sorted(pskills.intersection(jskills))
    missing = sorted(jskills.difference(pskills))

    # Simple score: percent of job keywords covered by candidate evidence
    score = 0.0
    if len(jskills) > 0:
        score = round((len(overlap) / len(jskills)) * 100.0, 2)

    evidence_map = {k: ("resume" if k in overlap else "missing") for k in sorted(jskills)}

    rationale = [
        f"Matched {len(overlap)} of {len(jskills)} job keywords.",
        f"Overlap: {', '.join(overlap) if overlap else 'None'}",
        f"Missing: {', '.join(missing) if missing else 'None'}",
    ]

    return MatchResult(
        run_id=run_id,
        profile_path=profile_path,
        job_path=job_path,
        overlap_skills=overlap,
        missing_skills=missing,
        score=score,
        rationale=rationale,
        evidence_map=evidence_map,
    )


def write_match_result(result: MatchResult, out_dir: str = "outputs/matching") -> Path:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = Path(out_dir) / f"match_result_{result.version}_{ts}.json"
    path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return path
