from __future__ import annotations

from careeros.ranking.service import rank_all_jobs


def run(*, profile_path: str, top_n: int, run_id: str, job_paths: list[str]):
    return rank_all_jobs(profile_path=profile_path, top_n=top_n, run_id=run_id, job_paths=job_paths)
