from careeros.parsing.schema import EvidenceProfile
from careeros.generation.schema import ApplicationPackage, ResumeBullet, CoverLetterDraft
from careeros.guardrails.service import validate_package_against_evidence


def _pkg(text: str) -> ApplicationPackage:
    return ApplicationPackage(
        run_id="r1",
        profile_path="p.json",
        job_path="j.json",
        bullets=[ResumeBullet(text=text)],
        evidence_skills=["python", "docker"],
        cover_letter=CoverLetterDraft(subject="s", paragraphs=["Thank you hiring team"]),
        qa_stubs={"Why fit?": "Because I built APIs."},
    )


def test_guardrails_blocks_real_unsupported_tool():
    profile = EvidenceProfile(raw_text="x", skills=["python", "docker"], titles=[], domains=[])
    pkg = _pkg("Built pipelines using python and docker and Snowflake")
    report = validate_package_against_evidence(profile, pkg, run_id="r2", package_path="pkg.json")
    assert report.status == "blocked"
    assert "snowflake" in (report.findings[0].unsupported_terms or [])


def test_guardrails_does_not_block_common_words():
    profile = EvidenceProfile(raw_text="x", skills=["python", "docker"], titles=[], domains=[])
    pkg = _pkg("Thank you team for your time")  # should not be treated as skills
    report = validate_package_against_evidence(profile, pkg, run_id="r3", package_path="pkg.json")
    assert report.status == "pass"
