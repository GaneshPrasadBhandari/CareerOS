import json
from pathlib import Path

from careeros.parsing.schema import EvidenceProfile
from careeros.generation.schema import ApplicationPackage, ResumeBullet, CoverLetterDraft
from careeros.guardrails.service import validate_package_against_evidence


def test_orchestrator_guardrail_block_rule():
    profile = EvidenceProfile(raw_text="x", skills=["python", "docker"], titles=[], domains=[])
    pkg = ApplicationPackage(
        run_id="r1",
        profile_path="p.json",
        job_path="j.json",
        bullets=[ResumeBullet(text="Built pipelines using Python, Docker, Snowflake")],
        evidence_skills=["python", "docker"],
        cover_letter=CoverLetterDraft(subject="s", paragraphs=["Hello"]),
        qa_stubs={"Why fit?": "x"},
    )
    report = validate_package_against_evidence(profile, pkg, run_id="r1", package_path="pkg.json")
    assert report.status == "blocked"
