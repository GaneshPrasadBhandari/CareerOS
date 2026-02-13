# src/careeros/ranking/service.py

from __future__ import annotations
import glob
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from careeros.parsing.schema import EvidenceProfile
from careeros.jobs.schema import JobPost
from careeros.matching.service import compute_match
from careeros.ranking.schema import RankedItem, RankedShortlist

logger = logging.getLogger(__name__)

def write_shortlist(shortlist: RankedShortlist, out_dir: str = "outputs/ranking") -> Path:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    # Using version and ts for unique artifact identification
    path = out_path / f"shortlist_{shortlist.run_id}_{ts}.json"
    path.write_text(shortlist.model_dump_json(indent=2), encoding="utf-8")
    return path

def rank_all_jobs(
    profile_path: str,
    top_n: int,
    run_id: str,
    jobs_dir: str = "outputs/jobs",
    job_paths: Optional[list[str]] = None,
) -> RankedShortlist:
    profile = EvidenceProfile.model_validate_json(Path(profile_path).read_text(encoding="utf-8"))

    # Search either provided explicit job paths or jobs_dir artifacts
    job_files = sorted(job_paths) if job_paths else sorted(glob.glob(f"{jobs_dir}/job_post_v1_*.json"))
    if not job_files:
        raise ValueError(f"No job_post artifacts found in {jobs_dir}. Run Phase 1/2 ingestion first.")

    items = []
    for jf in job_files:
        try:
            job = JobPost.model_validate_json(Path(jf).read_text(encoding="utf-8"))
            mr = compute_match(profile, job, run_id, profile_path=profile_path, job_path=jf)

            reasons = [
                f"Match Score: {mr.score}%",
                f"Key Overlap: {', '.join(mr.overlap_skills[:5]) if mr.overlap_skills else 'None'}",
                f"Missing Gaps: {len(mr.missing_skills)} identified"
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
        except Exception as e:
            logger.error(f"Failed to rank job {jf}: {str(e)}")
            continue # Don't crash the whole ranking if one file is corrupt

    # Sort and slice
    items_sorted = sorted(items, key=lambda x: x.score, reverse=True)
    
    shortlist = RankedShortlist(
        run_id=run_id, 
        profile_path=profile_path, 
        items=items_sorted[:top_n], 
        top_n=top_n,
        timestamp=datetime.utcnow().isoformat() # Recommendation: add this to schema
    )
    
    return shortlist