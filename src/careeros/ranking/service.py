from __future__ import annotations

import glob
from pathlib import Path
from datetime import datetime

from careeros.parsing.schema import EvidenceProfile
from careeros.jobs.schema import JobPost
from careeros.matching.service import compute_match
from careeros.ranking.schema import RankedItem, RankedShortlist


def write_shortlist(shortlist: RankedShortlist, out_dir: str = "outputs/ranking") -> Path:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = Path(out_dir) / f"shortlist_{shortlist.version}_{ts}.json"
    path.write_text(shortlist.model_dump_json(indent=2), encoding="utf-8")
    return path


def rank_all_jobs(profile_path: str, top_n: int, run_id: str) -> RankedShortlist:
    profile = EvidenceProfile.model_validate_json(Path(profile_path).read_text(encoding="utf-8"))

    job_files = sorted(glob.glob("outputs/jobs/job_post_v1_*.json"))
    if not job_files:
        raise ValueError("No job_post artifacts found. Run L3 first.")

    items = []
    for jf in job_files:
        job = JobPost.model_validate_json(Path(jf).read_text(encoding="utf-8"))
        mr = compute_match(profile, job, run_id, profile_path=profile_path, job_path=jf)


        reasons = [
            f"Score {mr.score} based on keyword coverage.",
            f"Overlap: {', '.join(mr.overlap_skills) if mr.overlap_skills else 'None'}",
        ]
        items.append(
            RankedItem(
                job_path=jf,
                score=mr.score,
                overlap_skills=mr.overlap_skills,
                missing_skills=mr.missing_skills,
                reasons=reasons,
            )
        )

    items_sorted = sorted(items, key=lambda x: x.score, reverse=True)
    return RankedShortlist(run_id=run_id, profile_path=profile_path, items=items_sorted[:top_n], top_n=top_n)
