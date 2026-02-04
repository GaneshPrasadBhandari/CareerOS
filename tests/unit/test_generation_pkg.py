from careeros.parsing.schema import EvidenceProfile
from careeros.jobs.schema import JobPost
from careeros.generation.service import build_package

def test_build_package_creates_bullets_and_cover():
    p = EvidenceProfile(raw_text="x", skills=["python", "docker", "mlflow"], titles=[], domains=[])
    j = JobPost(raw_text="y", keywords=["python", "docker"])
    pkg = build_package(p, j, run_id="1", profile_path="p.json", job_path="j.json", overlap_skills=["python", "docker"])
    assert len(pkg.bullets) >= 1
    assert pkg.cover_letter.subject
