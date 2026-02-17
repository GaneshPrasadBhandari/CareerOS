from careeros.parsing.schema import EvidenceProfile
from careeros.jobs.schema import JobPost
from careeros.matching.service import compute_match

def test_compute_match_scores_overlap():
    p = EvidenceProfile(raw_text="x", skills=["python", "docker", "mlflow"], titles=[], domains=[])
    j = JobPost(raw_text="y", keywords=["python", "kubernetes", "docker"])
    r = compute_match(p, j, run_id="1", profile_path="p.json", job_path="j.json")
    assert r.score == 66.67
    assert "python" in r.overlap_skills
    assert "kubernetes" in r.missing_skills
