from fastapi import FastAPI

from careeros.core.settings import load_settings
from careeros.core.logging import get_logger, new_run_id, log_event

from careeros.intake.schema import IntakeBundle
from careeros.intake.service import write_intake_bundle

from pydantic import BaseModel
from careeros.parsing.service import build_profile_from_text, write_profile

from careeros.core.logging import get_logger, new_run_id, log_event, log_exception

from pydantic import BaseModel
from careeros.jobs.service import build_jobpost_from_text, write_jobpost

from pathlib import Path
import glob
import json

from careeros.parsing.schema import EvidenceProfile
from careeros.jobs.schema import JobPost
from careeros.matching.service import compute_match, write_match_result


settings = load_settings()
logger = get_logger()

app = FastAPI(title="CareerOS API", version="0.1.0")


from fastapi import Request
from fastapi.responses import JSONResponse

logger = get_logger()


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    run_id = new_run_id()
    log_exception(logger, "unhandled_exception", run_id, exc, path=str(request.url.path))
    return JSONResponse(
        status_code=500,
        content={"status": "error", "code": "internal_error", "message": "Unexpected error", "run_id": run_id},
    )



@app.get("/")
def root():
    run_id = new_run_id()
    log_event(logger, "api_root_called", run_id, env=settings.env)
    return {"service": "CareerOS API", "status": "ok", "endpoints": ["/health", "/version"], "run_id": run_id}


@app.get("/health")
def health():
    run_id = new_run_id()
    log_event(logger, "api_health_called", run_id, env=settings.env)
    return {"status": "ok", "service": "CareerOS API", "run_id": run_id}


@app.get("/version")
def version():
    run_id = new_run_id()
    log_event(logger, "api_version_called", run_id, env=settings.env)
    return {
        "name": "CareerOS",
        "api_version": "0.1.0",
        "env": settings.env,
        "demo_mode": settings.demo_mode,
        "orchestration_mode": settings.orchestration_mode,
        "run_id": run_id,
    }


@app.post("/intake")
def create_intake(bundle: IntakeBundle):
    run_id = new_run_id()
    out_path = write_intake_bundle(bundle)
    log_event(logger, "intake_created", run_id, path=str(out_path))
    return {"status": "ok", "path": str(out_path), "run_id": run_id}


class ProfileRequest(BaseModel):
    candidate_name: str | None = None
    resume_text: str

@app.post("/profile")
def create_profile(req: ProfileRequest):
    run_id = new_run_id()
    profile = build_profile_from_text(req.resume_text, candidate_name=req.candidate_name)
    out_path = write_profile(profile)
    log_event(logger, "profile_created", run_id, path=str(out_path), skills=len(profile.skills))
    return {"status": "ok", "path": str(out_path), "skills": profile.skills, "run_id": run_id}


@app.get("/debug/error")
def debug_error():
    raise RuntimeError("Forced error to verify logging + exception handling")



class JobIngestRequest(BaseModel):
    url: str | None = None
    job_text: str

@app.post("/jobs/ingest")
def ingest_job(req: JobIngestRequest):
    run_id = new_run_id()
    job = build_jobpost_from_text(req.job_text, url=req.url)
    out_path = write_jobpost(job)
    log_event(logger, "job_ingested", run_id, path=str(out_path), keywords=len(job.keywords))
    return {"status": "ok", "path": str(out_path), "keywords": job.keywords, "run_id": run_id}



#Add API endpoint: run matching on the latest artifacts
def latest_file(pattern: str) -> str | None:
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None

@app.post("/match/run")
def run_match():
    run_id = new_run_id()

    profile_fp = latest_file("outputs/profile/profile_v1_*.json")
    job_fp = latest_file("outputs/jobs/job_post_v1_*.json")

    if not profile_fp or not job_fp:
        return {"status": "error", "message": "Missing profile or job artifacts. Run L2 and L3 first.", "run_id": run_id}

    profile = EvidenceProfile.model_validate_json(Path(profile_fp).read_text(encoding="utf-8"))
    job = JobPost.model_validate_json(Path(job_fp).read_text(encoding="utf-8"))

    result = compute_match(profile, job, run_id, profile_fp, job_fp)
    out_path = write_match_result(result)

    log_event(logger, "match_completed", run_id, score=result.score, path=str(out_path))
    return {"status": "ok", "path": str(out_path), "score": result.score, "run_id": run_id, "overlap": result.overlap_skills}
