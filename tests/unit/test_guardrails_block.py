from careeros.parsing.schema import EvidenceProfile
from careeros.jobs.schema import JobPost
from careeros.generation.service import build_package
from careeros.guardrails.service import validate_package_against_evidence

def test_guardrails_blocks_unsupported_skill():
    profile = EvidenceProfile(raw_text="x", skills=["python", "docker"], titles=[], domains=[])
    job = JobPost(raw_text="y", keywords=["python", "docker"])
    pkg = build_package(profile, job, run_id="1", profile_path="p.json", job_path="j.json", overlap_skills=["python", "docker"])
    # inject unsupported claim
    pkg.bullets[0].text += " and Snowflake"
    report = validate_package_against_evidence(profile, pkg, run_id="2", package_path="pkg.json")
    assert report.status == "blocked"
