from careeros.parsing.schema import EvidenceProfile
from careeros.jobs.schema import JobPost
from careeros.evidence.service import retrieve_chunks_for_skills
from careeros.generation.service import build_grounded_package_v2


def test_build_grounded_package_v2_has_citations():
    profile = EvidenceProfile(raw_text="x", skills=["Python", "Docker", "MLflow"], titles=[], domains=[])
    job = JobPost(raw_text="y", title="ML Engineer", keywords=["python", "docker"])

    retrieval = retrieve_chunks_for_skills(profile, ["python", "docker"])
    skill_to_chunk_ids = {}
    for ch in retrieval.chunks:
        for tag in ch.tags:
            skill_to_chunk_ids.setdefault(tag, []).append(ch.chunk_id)

    pkg = build_grounded_package_v2(
        profile=profile,
        job=job,
        run_id="run_1",
        profile_path="p.json",
        job_path="j.json",
        overlap_skills=["python", "docker"],
        skill_to_chunk_ids=skill_to_chunk_ids,
    )

    assert pkg.version == "v2"
    assert pkg.citations_required is True
    assert pkg.citations_complete is True
    assert len(pkg.bullets) >= 1
    assert all(len(b.evidence_chunk_ids) > 0 for b in pkg.bullets)
