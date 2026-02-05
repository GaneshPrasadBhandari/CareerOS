from __future__ import annotations
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

from careeros.ranking.service import rank_all_jobs, write_shortlist

from careeros.ranking.schema import RankedShortlist
from careeros.parsing.schema import EvidenceProfile
from careeros.jobs.schema import JobPost
from careeros.generation.service import build_package, write_application_package

from careeros.guardrails.service import validate_package_against_evidence, write_validation_report, latest
from careeros.guardrails.schema import ValidationReport
from careeros.generation.schema import ApplicationPackage

from fastapi import FastAPI, HTTPException

# NEW imports for P8
from careeros.export.schema import ExportRequest, ExportResult
from careeros.export.service import export_latest_validated_package
from careeros.tracking.schema import ApplicationRecord, ApplicationStatus
from careeros.tracking.service import append_jsonl, update_status_jsonl, _utc_now

from careeros.analytics.schema import FunnelMetrics, ListApplicationsResponse
from careeros.analytics.service import list_applications, compute_metrics, get_application
from fastapi import Query

from careeros.followups.service import (
    generate_next_actions,
    write_action_queue,
    load_action_queue,
    latest_action_queue_path,
    action_queue_to_dict,
)





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



#Add API endpoint: /rank/run for raniking jobs
@app.post("/rank/run")
def run_ranking(top_n: int = 3):
    run_id = new_run_id()

    profile_files = sorted(glob.glob("outputs/profile/profile_v1_*.json"))
    if not profile_files:
        return {"status": "error", "message": "No profile artifacts found. Run L2 first.", "run_id": run_id}

    profile_path = profile_files[-1]

    try:
        shortlist = rank_all_jobs(profile_path=profile_path, top_n=top_n, run_id=run_id)
        out_path = write_shortlist(shortlist)
        log_event(logger, "ranking_completed", run_id, top_n=top_n, path=str(out_path))
        return {"status": "ok", "path": str(out_path), "run_id": run_id, "top_n": top_n, "items": [i.model_dump() for i in shortlist.items]}
    except Exception as e:
        log_exception(logger, "ranking_failed", run_id, e)
        return {"status": "error", "message": str(e), "run_id": run_id}




#Add API endpoint: generate package for Top-1 job
#Add helper to get latest file
def latest(pattern: str) -> str | None:
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None

#Add endpoint
@app.post("/generate/package")
def generate_package():
    run_id = new_run_id()

    shortlist_fp = latest("outputs/ranking/shortlist_v1_*.json")
    if not shortlist_fp:
        return {"status": "error", "message": "No shortlist found. Run P5 ranking first.", "run_id": run_id}

    shortlist = RankedShortlist.model_validate_json(Path(shortlist_fp).read_text(encoding="utf-8"))
    if not shortlist.items:
        return {"status": "error", "message": "Shortlist is empty.", "run_id": run_id}

    # Top-1 job
    top_item = shortlist.items[0]
    profile_fp = shortlist.profile_path
    job_fp = top_item.job_path

    profile = EvidenceProfile.model_validate_json(Path(profile_fp).read_text(encoding="utf-8"))
    job = JobPost.model_validate_json(Path(job_fp).read_text(encoding="utf-8"))

    pkg = build_package(
        profile=profile,
        job=job,
        run_id=run_id,
        profile_path=profile_fp,
        job_path=job_fp,
        overlap_skills=top_item.overlap_skills,
    )

    out_path = write_application_package(pkg)
    log_event(logger, "package_generated", run_id, path=str(out_path), job_path=job_fp)
    return {"status": "ok", "path": str(out_path), "run_id": run_id}


#Add API endpoint: validate latest package
#Add endpoint
@app.post("/guardrails/validate")
def validate_latest_package():
    run_id = new_run_id()

    pkg_fp = latest("exports/packages/application_package_v1_*.json")
    profile_fp = latest("outputs/profile/profile_v1_*.json")

    if not pkg_fp or not profile_fp:
        return {"status": "error", "message": "Missing package or profile artifacts. Run P2 and P6 first.", "run_id": run_id}

    profile = EvidenceProfile.model_validate_json(Path(profile_fp).read_text(encoding="utf-8"))
    pkg = ApplicationPackage.model_validate_json(Path(pkg_fp).read_text(encoding="utf-8"))

    report = validate_package_against_evidence(profile, pkg, run_id, pkg_fp)
    out_path = write_validation_report(report)

    if report.status == "blocked":
        log_event(logger, "guardrails_blocked", run_id, path=str(out_path))
        return {"status": "blocked", "path": str(out_path), "run_id": run_id, "findings": [f.model_dump() for f in report.findings]}

    log_event(logger, "guardrails_passed", run_id, path=str(out_path))
    return {"status": "pass", "path": str(out_path), "run_id": run_id}



#add P8 routes
# ---- P8: Export + Apply Tracking ----

TRACKING_PATH = "outputs/apply_tracking/applications_v1.jsonl"

@app.post("/export/package", response_model=ExportResult)
def export_package(req: ExportRequest):
    try:
        meta = export_latest_validated_package(
            package_path=req.package_path,
            validation_report_path=req.validation_report_path,
            out_dir=req.out_dir,
            export_docx=req.export_docx,
            export_pdf=req.export_pdf,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        # blocked by guardrails
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")

    record = ApplicationRecord(
        application_id=meta["application_id"],
        run_id=meta["run_id"],
        job_path=None,  # optional; can be derived later from meta["package_path"] content
        package_path=meta["package_path"],
        validation_report_path=meta["validation_report_path"],
        export_docx_path=meta["docx_path"],
        export_pdf_path=meta["pdf_path"],
        status="exported",
        created_at_utc=_utc_now(),
        updated_at_utc=_utc_now(),
    )
    append_jsonl(TRACKING_PATH, record)

    return ExportResult(
        application_id=record.application_id,
        run_id=record.run_id,
        package_path=record.package_path,
        validation_report_path=record.validation_report_path,
        docx_path=record.export_docx_path,
        pdf_path=record.export_pdf_path,
        status=record.status,
    )


class UpdateStatusRequest(BaseModel):
    application_id: str
    new_status: ApplicationStatus


@app.post("/apply/update_status", response_model=ApplicationRecord)
def apply_update_status(req: UpdateStatusRequest):
    rec = update_status_jsonl(TRACKING_PATH, req.application_id, req.new_status)
    if rec is None:
        raise HTTPException(status_code=404, detail="application_id not found in tracking file")
    return 



#add route for P9
@app.get("/applications/list", response_model=ListApplicationsResponse)
def applications_list(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
):
    return list_applications(TRACKING_PATH, status=status, limit=limit, newest_first=True)


@app.get("/applications/metrics", response_model=FunnelMetrics)
def applications_metrics():
    return compute_metrics(TRACKING_PATH)


@app.get("/applications/{application_id}")
def applications_get(application_id: str):
    rec = get_application(TRACKING_PATH, application_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="application_id not found")
    return rec


#add api routes for p10
@app.post("/followups/generate")
def followups_generate(followup_days: int = 3, stale_days: int = 14):
    queue = generate_next_actions(TRACKING_PATH, followup_days=followup_days, stale_days=stale_days)
    path = write_action_queue(queue)
    return {"status": "ok", "path": str(path), "total": queue.total}

@app.get("/followups/latest")
def followups_latest():
    try:
        path = latest_action_queue_path()
        if not path:
            return {
                "status": "error",
                "code": "not_found",
                "message": "No followups queue found yet. Run /followups/generate first.",
            }

        q = load_action_queue(path)
        return {
            "status": "ok",
            "path": path,
            "queue": action_queue_to_dict(q),
        }

    except Exception as e:
        return {
            "status": "error",
            "code": "internal_error",
            "message": f"Unexpected error: {e}",
        }

