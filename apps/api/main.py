from fastapi import FastAPI

from careeros.core.settings import load_settings
from careeros.core.logging import get_logger, new_run_id, log_event

from careeros.intake.schema import IntakeBundle
from careeros.intake.service import write_intake_bundle

from pydantic import BaseModel
from careeros.parsing.service import build_profile_from_text, write_profile



settings = load_settings()
logger = get_logger()

app = FastAPI(title="CareerOS API", version="0.1.0")


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
