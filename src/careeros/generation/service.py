from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import List, Dict

from careeros.parsing.schema import EvidenceProfile
from careeros.jobs.schema import JobPost
from careeros.generation.schema import ApplicationPackage, ApplicationPackageV2, ResumeBullet, CoverLetterDraft

def _bullet_templates() -> List[str]:
    # Keep these “safe”: no fake metrics, no invented employers, no invented years.
    return [
        "Designed and delivered production-ready AI/ML solutions using {skills}.",
        "Built scalable APIs and workflows using {skills} to support real-world deployments.",
        "Implemented MLOps practices for reproducibility and tracking using {skills}.",
        "Developed GenAI/RAG capabilities with {skills} for grounded enterprise outputs.",
    ]


def generate_bullets(overlap_skills: List[str]) -> List[ResumeBullet]:
    # Use up to 5 skills to keep bullets readable
    skills = [s for s in overlap_skills][:5]
    skills_str = ", ".join(skills) if skills else "core engineering practices"

    bullets = []
    for t in _bullet_templates()[:3]:
        bullets.append(ResumeBullet(text=t.format(skills=skills_str), evidence_skills=skills))
    return bullets


def generate_cover_letter(profile: EvidenceProfile, job: JobPost, overlap_skills: List[str]) -> CoverLetterDraft:
    role = job.title or "the role"
    skills_str = ", ".join(overlap_skills[:6]) if overlap_skills else ", ".join(profile.skills[:6]) or "relevant skills"

    subject = f"Application for {role}"

    p1 = f"Hello Hiring Team, I’m applying for {role}. My background aligns strongly with the role’s needs, particularly in {skills_str}."
    p2 = "I focus on building production-grade systems: clean APIs, reliable pipelines, and measurable outcomes. I value traceability, safety, and governance in AI delivery."
    p3 = "If helpful, I can share examples of end-to-end work covering design, implementation, testing, and deployment. Thank you for your time and consideration."

    return CoverLetterDraft(subject=subject, paragraphs=[p1, p2, p3])


def write_application_package(pkg: ApplicationPackage, out_dir: str = "exports/packages") -> Path:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    # job filename safe hint
    hint = Path(pkg.job_path).stem.replace("job_post_", "")
    path = Path(out_dir) / f"application_package_{pkg.version}_{hint}_{ts}.json"
    path.write_text(pkg.model_dump_json(indent=2), encoding="utf-8")
    return path


def build_package(profile: EvidenceProfile, job: JobPost, run_id: str, profile_path: str, job_path: str, overlap_skills: List[str]) -> ApplicationPackage:
    bullets = generate_bullets(overlap_skills)
    cover = generate_cover_letter(profile, job, overlap_skills)
    qa = {
        "Why are you a fit for this role?": f"My experience in {', '.join(overlap_skills[:6]) if overlap_skills else 'relevant areas'} matches the role requirements, and I build production-ready systems with strong engineering discipline.",
        "What are your strongest skills?": ", ".join(overlap_skills[:8]) if overlap_skills else ", ".join(profile.skills[:8]),
    }

    return ApplicationPackage(
        run_id=run_id,
        profile_path=profile_path,
        job_path=job_path,
        job_title_hint=job.title,
        company_hint=job.company,
        bullets=bullets,
        cover_letter=cover,
        qa_stubs=qa,
    )



def generate_grounded_bullets(overlap_skills: List[str], skill_to_chunk_ids: Dict[str, List[str]]) -> List[ResumeBullet]:
    skills = [s for s in overlap_skills][:5]
    skills_str = ", ".join(skills) if skills else "core engineering practices"

    bullets: List[ResumeBullet] = []
    for t in _bullet_templates()[:3]:
        cited_chunk_ids: List[str] = []
        for s in skills:
            cited_chunk_ids.extend(skill_to_chunk_ids.get(s.lower(), []))
        cited_chunk_ids = sorted(set(cited_chunk_ids))
        bullets.append(
            ResumeBullet(
                text=t.format(skills=skills_str),
                evidence_skills=skills,
                evidence_chunk_ids=cited_chunk_ids,
            )
        )
    return bullets


def write_application_package_v2(pkg: ApplicationPackageV2, out_dir: str = "exports/packages") -> Path:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    hint = Path(pkg.job_path).stem.replace("job_post_", "")
    path = Path(out_dir) / f"application_package_{pkg.version}_{hint}_{ts}.json"
    path.write_text(pkg.model_dump_json(indent=2), encoding="utf-8")
    return path


def build_grounded_package_v2(
    profile: EvidenceProfile,
    job: JobPost,
    run_id: str,
    profile_path: str,
    job_path: str,
    overlap_skills: List[str],
    skill_to_chunk_ids: Dict[str, List[str]],
) -> ApplicationPackageV2:
    bullets = generate_grounded_bullets(overlap_skills, skill_to_chunk_ids)
    cover = generate_cover_letter(profile, job, overlap_skills)
    qa = {
        "Why are you a fit for this role?": f"My experience in {', '.join(overlap_skills[:6]) if overlap_skills else 'relevant areas'} matches the role requirements, and I can provide cited evidence for each claim.",
        "What are your strongest skills?": ", ".join(overlap_skills[:8]) if overlap_skills else ", ".join(profile.skills[:8]),
    }
    citations_complete = all(len(b.evidence_chunk_ids) > 0 for b in bullets) if bullets else False

    return ApplicationPackageV2(
        run_id=run_id,
        profile_path=profile_path,
        job_path=job_path,
        job_title_hint=job.title,
        company_hint=job.company,
        bullets=bullets,
        cover_letter=cover,
        qa_stubs=qa,
        citations_required=True,
        citations_complete=citations_complete,
    )