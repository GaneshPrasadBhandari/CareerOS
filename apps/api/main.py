from fastapi import FastAPI

from src.careeros.core.settings import load_settings
from src.careeros.core.logging import get_logger, new_run_id, log_event
from src.careeros.intake.schema import IntakeBundle
from src.careeros.intake.service import write_intake_bundle


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
