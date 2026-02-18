from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import List, Dict

from careeros.parsing.schema import EvidenceProfile
from careeros.jobs.schema import JobPost
from careeros.generation.schema import ApplicationPackage, ApplicationPackageV2, ResumeBullet, CoverLetterDraft, TailoredResume

def _bullet_templates() -> List[str]:
    # Keep these “safe”: no fake metrics, no invented employers, no invented years.
    return [
        "Designed and delivered production-ready AI/ML solutions using {skills}, with clear ownership from design to rollout.",
        "Built scalable APIs and workflow services using {skills}, emphasizing reliability, observability, and maintainability.",
        "Implemented MLOps and evaluation practices using {skills} to improve reproducibility and deployment confidence.",
        "Developed retrieval/GenAI capabilities with {skills} while applying guardrails and evidence-backed outputs.",
        "Partnered cross-functionally to translate business requirements into shipped features using {skills}.",
    ]


def generate_bullets(overlap_skills: List[str]) -> List[ResumeBullet]:
    # Use up to 8 skills so ATS scanners see more direct keyword overlap.
    skills = [s for s in overlap_skills][:8]
    skills_str = ", ".join(skills) if skills else "core engineering practices"

    bullets = []
    for t in _bullet_templates()[:5]:
        bullets.append(ResumeBullet(text=t.format(skills=skills_str), evidence_skills=skills))
    return bullets



def generate_tailored_resume(profile: EvidenceProfile, job: JobPost, overlap_skills: List[str]) -> TailoredResume:
    role = job.title or (profile.titles[0] if profile.titles else "Target Role")
    company = job.company or "Target Company"
    key_skills = overlap_skills[:10] if overlap_skills else profile.skills[:10]

    summary = (
        f"Engineer focused on {role} opportunities with hands-on delivery across APIs, data/ML workflows, "
        f"and production reliability. Strong alignment with {company} requirements through practical execution "
        f"in {', '.join(key_skills[:6]) if key_skills else 'software engineering fundamentals'}."
    )

    exp_highlights = [b.text for b in generate_bullets(key_skills)[:4]]
    proj_highlights = []
    for prj in profile.projects[:3]:
        line = f"{prj.name or 'Project'}: "
        if prj.stack:
            line += f"Tech stack {', '.join(prj.stack[:6])}. "
        if prj.highlights:
            line += prj.highlights[0]
        proj_highlights.append(line.strip())

    if not proj_highlights:
        proj_highlights = [
            "Built end-to-end feature pipelines with measurable quality checks and deployment readiness.",
            "Implemented testing and observability patterns to improve stability and iteration speed.",
        ]

    return TailoredResume(
        headline=f"{profile.candidate_name or 'Candidate'} - {role}",
        professional_summary=summary,
        core_skills=key_skills,
        experience_highlights=exp_highlights,
        projects_highlights=proj_highlights,
    )

def generate_cover_letter(profile: EvidenceProfile, job: JobPost, overlap_skills: List[str]) -> CoverLetterDraft:
    role = job.title or "the role"
    company = job.company or "your team"
    skills_str = ", ".join(overlap_skills[:8]) if overlap_skills else ", ".join(profile.skills[:8]) or "relevant skills"

    subject = f"Application for {role}"

    p1 = (
        f"Dear Hiring Manager, I am excited to apply for {role} at {company}. "
        f"My recent projects align with the role requirements, especially across {skills_str}."
    )
    p2 = (
        "I bring a product-minded engineering approach: defining requirements clearly, implementing maintainable APIs and pipelines, "
        "and validating quality with tests and guardrails before release."
    )
    p3 = (
        "My experience includes end-to-end delivery across profile parsing, matching, ranking, and application generation workflows, "
        "with attention to reliability, observability, and compliance constraints."
    )
    p4 = (
        "I would welcome the opportunity to discuss how I can contribute quickly to your roadmap. "
        "Thank you for your consideration."
    )

    return CoverLetterDraft(subject=subject, paragraphs=[p1, p2, p3, p4])


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
    tailored_resume = generate_tailored_resume(profile, job, overlap_skills)
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
        tailored_resume=tailored_resume,
        cover_letter=cover,
        qa_stubs=qa,
    )



def generate_grounded_bullets(overlap_skills: List[str], skill_to_chunk_ids: Dict[str, List[str]]) -> List[ResumeBullet]:
    skills = [s for s in overlap_skills][:5]
    skills_str = ", ".join(skills) if skills else "core engineering practices"

    bullets: List[ResumeBullet] = []
    for t in _bullet_templates()[:5]:
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
    tailored_resume = generate_tailored_resume(profile, job, overlap_skills)
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
        tailored_resume=tailored_resume,
        cover_letter=cover,
        qa_stubs=qa,
        citations_required=True,
        citations_complete=citations_complete,
    )