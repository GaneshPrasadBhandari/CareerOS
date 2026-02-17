import json
from pathlib import Path

from careeros.orchestrator.service import run_p6_to_p11


def _write_profile(tmp_path: Path) -> str:
    p = tmp_path / "profile_v1_test.json"
    p.write_text(
        json.dumps(
            {
                "version": "v1",
                "candidate_name": "Test",
                "raw_text": "Python Docker",
                "skills": ["python", "docker"],
                "titles": [],
                "domains": [],
                "experiences": [],
                "projects": [],
            }
        ),
        encoding="utf-8",
    )
    return str(p)


def _write_job(tmp_path: Path) -> str:
    p = tmp_path / "job_post_v1_test.json"
    p.write_text(
        json.dumps(
            {
                "version": "v1",
                "source": "paste",
                "url": None,
                "raw_text": "Need Python and Docker",
                "keywords": ["python", "docker"],
            }
        ),
        encoding="utf-8",
    )
    return str(p)


def _ensure_dirs(tmp_path: Path):
    # Create the directories your services write into.
    # Orchestrator uses repo-relative paths; we switch cwd in test.
    (tmp_path / "outputs/profile").mkdir(parents=True, exist_ok=True)
    (tmp_path / "outputs/jobs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "outputs/ranking").mkdir(parents=True, exist_ok=True)
    (tmp_path / "outputs/guardrails").mkdir(parents=True, exist_ok=True)
    (tmp_path / "outputs/apply_tracking").mkdir(parents=True, exist_ok=True)
    (tmp_path / "outputs/followups").mkdir(parents=True, exist_ok=True)
    (tmp_path / "outputs/notifications").mkdir(parents=True, exist_ok=True)
    (tmp_path / "outputs/orchestrator").mkdir(parents=True, exist_ok=True)
    (tmp_path / "exports/packages").mkdir(parents=True, exist_ok=True)
    (tmp_path / "exports/submissions").mkdir(parents=True, exist_ok=True)


def _write_shortlist(tmp_path: Path, profile_path: str, job_path: str):
    p = tmp_path / "outputs/ranking/shortlist_v1_test.json"
    p.write_text(
        json.dumps(
            {
                "version": "v1",
                "run_id": "r",
                "created_at_utc": "2026-02-06T00:00:00Z",
                "profile_path": profile_path,
                "top_n": 1,
                "items": [
                    {
                        "job_path": job_path,
                        "score": 100,
                        "overlap_skills": ["python", "docker"],
                        "missing_skills": [],
                        "reasons": ["full overlap"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_orchestrator_runs_end_to_end(tmp_path, monkeypatch):
    """
    End-to-end unit test for P12:
    Uses deterministic artifacts and ensures orchestrator produces followups + drafts.
    """
    _ensure_dirs(tmp_path)
    monkeypatch.chdir(tmp_path)

    profile_path = _write_profile(tmp_path)
    job_path = _write_job(tmp_path)
    _write_shortlist(tmp_path, profile_path, job_path)

    out = run_p6_to_p11(followup_days=3, stale_days=14)

    assert out["final_status"] in ("ok", "blocked", "error")

    # If ok, ensure the output artifacts exist.
    if out["final_status"] == "ok":
        assert Path(out["outputs"]["package_path"]).exists()
        assert Path(out["outputs"]["validation_report_path"]).exists()
        assert Path(out["outputs"]["followups_path"]).exists()
        assert Path(out["outputs"]["drafts_path"]).exists()
        assert Path(out["path"]).exists()
