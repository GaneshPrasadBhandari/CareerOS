from __future__ import annotations

import sys
import os
from pathlib import Path

# This adds the root 'src' folder to the path
ROOT_DIR = Path(__file__).resolve().parents[2] 
sys.path.append(str(ROOT_DIR / "src"))

import glob
import importlib.util
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field


ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from careeros.core.settings import load_settings
from careeros.core.logging import get_logger, new_run_id, log_event, log_exception

# P1
from careeros.intake.schema import IntakeBundle
from careeros.intake.service import write_intake_bundle

# P2
from careeros.parsing.service import build_profile_from_text, write_profile
from careeros.parsing.schema import EvidenceProfile

# P3
from careeros.jobs.service import build_jobpost_from_text, write_jobpost
from careeros.jobs.schema import JobPost

# P4
from careeros.matching.service import compute_match, write_match_result

# P5
from careeros.ranking.service import rank_all_jobs, write_shortlist
from careeros.ranking.schema import RankedShortlist

# P6
from careeros.generation.service import build_package, write_application_package
from careeros.generation.schema import ApplicationPackage, ApplicationPackageV2
from careeros.guardrails.schema import ValidationFinding

# P7
from careeros.guardrails.service import validate_package_against_evidence, write_validation_report
from careeros.guardrails.schema import ValidationReport

# P8
from careeros.export.schema import ExportRequest, ExportResult
from careeros.export.service import export_latest_validated_package
from careeros.tracking.schema import ApplicationRecord, ApplicationStatus
from careeros.tracking.service import append_jsonl, update_status_jsonl, _utc_now

# P9
from careeros.analytics.schema import FunnelMetrics, ListApplicationsResponse
from careeros.analytics.service import list_applications, compute_metrics, get_application

# P10
from careeros.followups.service import (
    generate_next_actions,
    write_action_queue,
    load_action_queue,
    latest_action_queue_path,
    action_queue_to_dict,
)

# P11
from careeros.notifications.service import (
    generate_drafts_from_followups,
    write_drafts_bundle,
    load_drafts_bundle,
    latest_drafts_path,
    draft_bundle_to_dict,
)

# P12
from careeros.orchestrator.service import run_p6_to_p11


#P13
from careeros.agentic.state import OrchestratorState
from careeros.agentic.state_store import write_state
from careeros.agentic.tools.registry import ToolRegistry
from careeros.agentic.tools.spec import ToolSpec


#P14 
from careeros.agentic.p14_orchestrator import run_plan_p6_to_p11
from careeros.evidence.service import retrieve_chunks_for_skills
from careeros.generation.service import build_grounded_package_v2, write_application_package_v2


#p15
from apps.api.routes import orchestrator

from careeros.phase3.contracts import AgentTaskInput
from careeros.phase3.service import validate_contract, dry_run_agent_step, PHASE3_STEPS
from careeros.phase3.langgraph_flow import run_langgraph_pipeline
from careeros.phase3.next_steps import (
    write_p22_approval_decision,
    latest_p22_approval,
    p23_memory_upsert,
    p23_memory_get,
    p24_evaluate_run,
    parser_extract,
    vision_ocr,
    connector_ingest,
    p25_automation_run,
    latest_p25_trace,
)
from careeros.phase3.evaluator_v2 import evaluate_run_v2, latest_eval_v2, EvalWeights
from careeros.phase3.system_checks import run_system_health_checks
from careeros.feedback.service import append_feedback, append_employer_signal, list_feedback
from careeros.evidence.vector_store import vector_capabilities
from careeros.integrations.job_boards.sources import discover_job_urls_for_roles


# ------------------------------------------------------------------------------
# App boot
# ------------------------------------------------------------------------------
settings = load_settings()
logger = get_logger()

app = FastAPI(title="CareerOS API", version="0.1.0")

_MULTIPART_AVAILABLE = importlib.util.find_spec("multipart") is not None


# ------------------------------------------------------------------------------
# P13 — Tool Registry (initial empty catalog; P14 will register real tools)
# ------------------------------------------------------------------------------
tool_registry = ToolRegistry()

@app.get("/tools")
def list_tools():
    run_id = new_run_id()
    log_event(logger, "tools_listed", run_id, count=len(tool_registry.list()))
    return {"status": "ok", "tools": tool_registry.describe(), "run_id": run_id}


class RunInitRequest(BaseModel):
    env: str | None = None
    orchestration_mode: str | None = None


@app.post("/runs/init")
def init_run(req: RunInitRequest):
    run_id = new_run_id()
    state = OrchestratorState(
        run_id=run_id,
        env=req.env or settings.env,
        orchestration_mode=req.orchestration_mode or settings.orchestration_mode,
    )
    fp = write_state(state)
    log_event(logger, "run_initialized", run_id, path=str(fp))
    return {"status": "ok", "run_id": run_id, "state_path": str(fp)}





# ------------------------------------------------------------------------------
# Global exception handler
# ------------------------------------------------------------------------------
@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    run_id = new_run_id()
    log_exception(logger, "unhandled_exception", run_id, exc, path=str(request.url.path))
    return JSONResponse(
        status_code=500,
        content={"status": "error", "code": "internal_error", "message": "Unexpected error", "run_id": run_id},
    )


# ------------------------------------------------------------------------------
# Small helpers
# ------------------------------------------------------------------------------
def latest_file(pattern: str) -> Optional[str]:
    files = glob.glob(pattern)
    if not files:
        return None
    return str(max(files, key=lambda f: Path(f).stat().st_mtime))




def _extract_pdf_text_bytes(raw: bytes) -> str:
    try:
        from pypdf import PdfReader
        import io

        reader = PdfReader(io.BytesIO(raw))
        txt = "\n".join((p.extract_text() or "") for p in reader.pages).strip()
        if txt:
            return txt
    except Exception:
        pass

    try:
        import fitz  # pymupdf

        doc = fitz.open(stream=raw, filetype="pdf")
        txt = "\n".join(page.get_text("text") for page in doc).strip()
        if txt:
            return txt
    except Exception:
        pass

    return ""


def _extract_upload_text(upload: UploadFile) -> str:
    name = (upload.filename or "").lower()
    raw = upload.file.read()

    if name.endswith(".pdf"):
        return _extract_pdf_text_bytes(raw)

    if name.endswith(".docx"):
        from docx import Document
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".docx") as tmp:
            tmp.write(raw)
            tmp.flush()
            doc = Document(tmp.name)
            return "\n".join(par.text for par in doc.paragraphs).strip()

    if name.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff")):
        try:
            import pytesseract
            from PIL import Image
            import io

            return pytesseract.image_to_string(Image.open(io.BytesIO(raw))).strip()
        except Exception:
            return ""

    return raw.decode("utf-8", errors="ignore").strip()


# ------------------------------------------------------------------------------
# Base endpoints
# ------------------------------------------------------------------------------
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




@app.get("/system/storage/status")
def system_storage_status():
    roots = {
        "outputs": str(Path("outputs").resolve()),
        "exports": str(Path("exports").resolve()),
        "data": str(Path("data").resolve()),
    }
    caps = vector_capabilities()
    vector_backend = str(caps.get("vector_db", "chroma"))
    return {
        "status": "ok",
        "storage": roots,
        "database": {"default": str(Path("mlflow.db").resolve())},
        "vector_db": {
            "enabled": vector_backend.lower() != "none",
            "backend": vector_backend,
            "embedding_model": caps.get("embedding_model"),
            "default": "Chroma local persistent DB at outputs/phase3/chroma",
            "note": "Set VECTOR_DB=qdrant and QDRANT_URL(+QDRANT_API_KEY) to use hosted Qdrant.",
        },
    }


@app.get("/system/automation/status")
def system_automation_status():
    caps = vector_capabilities()
    return {
        "status": "ok",
        "automation_layers": {
            "L1_intake_bootstrap": True,
            "L2_parsing": True,
            "L3_job_discovery": True,
            "L4_matching": True,
            "L5_ranking": True,
            "L6_generation": True,
            "L7_guardrails": True,
            "L8_llm_summary": True,
            "L9_vector_indexing": True,
            "L10_hitl_decision": True,
        },
        "integrations": caps,
        "required_for_full_web_discovery": ["SERPER_API_KEY or TAVILY_API_KEY"],
        "optional_for_js_heavy_portals": ["SCRAPINGBEE_API_KEY"],
        "required_for_hosted_qdrant": ["QDRANT_URL", "QDRANT_API_KEY(optional if public)"],
        "required_for_hf_summary": ["HF_TOKEN or HUGGINGFACE_API_KEY"],
        "ocr_for_image_uploads": ["Install tesseract binary + pytesseract + pillow"],
    }

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


# ------------------------------------------------------------------------------
# P1 — Intake
# ------------------------------------------------------------------------------
@app.post("/intake")
def create_intake(bundle: IntakeBundle):
    run_id = new_run_id()
    out_path = write_intake_bundle(bundle)
    log_event(logger, "intake_created", run_id, path=str(out_path))
    return {"status": "ok", "path": str(out_path), "run_id": run_id}


# ------------------------------------------------------------------------------
# P2 — Profile
# ------------------------------------------------------------------------------
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




class IntakeBootstrapRequest(BaseModel):
    candidate_name: str | None = None
    target_roles: list[str] = Field(default_factory=list)
    location: str | None = None
    remote_only: bool = True
    salary_min: int | None = None
    salary_max: int | None = None
    work_auth: str | None = None
    resume_text: str


@app.post("/intake/bootstrap")
def intake_bootstrap(req: IntakeBootstrapRequest):
    run_id = new_run_id()
    intake = IntakeBundle(
        candidate_name=req.candidate_name,
        target_roles=req.target_roles,
        constraints={
            "location": req.location,
            "remote_only": req.remote_only,
            "salary_min": req.salary_min,
            "salary_max": req.salary_max,
            "work_auth": req.work_auth,
            "relocation_ok": False,
        },
    )
    intake_path = write_intake_bundle(intake)
    profile = build_profile_from_text(req.resume_text, candidate_name=req.candidate_name)
    profile_path = write_profile(profile)
    log_event(logger, "intake_bootstrap_created", run_id, intake_path=str(intake_path), profile_path=str(profile_path))
    return {
        "status": "ok",
        "run_id": run_id,
        "intake_path": str(intake_path),
        "profile_path": str(profile_path),
        "skills": profile.skills,
        "details": {
            "message": "L1 intake and L2 profile bootstrap completed",
            "candidate_name": req.candidate_name,
            "target_roles": req.target_roles,
            "location": req.location,
            "jobs_discovery_ready": True,
        },
    }


@app.get("/debug/error")
def debug_error():
    raise RuntimeError("Forced error to verify logging + exception handling")


# ------------------------------------------------------------------------------
# P3 — Job ingestion
# ------------------------------------------------------------------------------
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


class JobDiscoverIngestRequest(BaseModel):
    roles: list[str] = Field(default_factory=list)
    location: str = "USA"
    max_per_source: int = Field(default=2, ge=1, le=5)
    daily_limit: int = Field(default=20, ge=1, le=60)
    timeout_s: int = Field(default=10, ge=4, le=45)
    recent_hours: int | None = Field(default=36, ge=1, le=240)


@app.post("/jobs/discover_ingest")
def jobs_discover_and_ingest(req: JobDiscoverIngestRequest):
    run_id = new_run_id()
    discovered = discover_job_urls_for_roles(
        roles=req.roles,
        location=req.location,
        max_per_source=req.max_per_source,
        daily_limit=req.daily_limit,
        recent_hours=req.recent_hours,
    )
    connector = connector_ingest({"urls": discovered.get("urls", []), "timeout_s": req.timeout_s})

    ingested_paths: list[str] = []

    # Always ingest discovered snippets first, so automation still works if remote pages block scraping.
    for jt in discovered.get("job_texts", []):
        raw_text = str(jt or "").strip()
        if not raw_text:
            continue
        out_path = write_jobpost(build_jobpost_from_text(raw_text))
        ingested_paths.append(str(out_path))

    for item in connector.get("items", []):
        raw_text = str(item.get("text") or "").strip()
        if not raw_text:
            continue
        out_path = write_jobpost(build_jobpost_from_text(raw_text, url=item.get("url")))
        ingested_paths.append(str(out_path))

    status = "ok" if ingested_paths else "degraded"
    log_event(
        logger,
        "jobs_discover_ingest_completed",
        run_id,
        discovered_urls=len(discovered.get("urls", [])),
        ingested=len(ingested_paths),
        status=status,
    )
    return {
        "status": status,
        "run_id": run_id,
        "sources": discovered.get("sources", []),
        "discovery": {
            "status": discovered.get("status"),
            "urls": discovered.get("urls", []),
            "errors": discovered.get("errors", []),
        },
        "connector": {
            "status": connector.get("status"),
            "items_ingested": connector.get("items_ingested", 0),
            "errors": connector.get("errors", []),
        },
        "job_paths": ingested_paths,
    }


# ------------------------------------------------------------------------------
# P4 — Matching (latest profile + latest job)
# ------------------------------------------------------------------------------
@app.post("/match/run")
def run_match():
    run_id = new_run_id()

    profile_fp = latest_file("outputs/profile/profile_v1_*.json")
    job_fp = latest_file("outputs/jobs/job_post_v1_*.json")

    if not profile_fp or not job_fp:
        return {"status": "error", "message": "Missing profile or job artifacts. Run P2 and P3 first.", "run_id": run_id}

    profile = EvidenceProfile.model_validate_json(Path(profile_fp).read_text(encoding="utf-8"))
    job = JobPost.model_validate_json(Path(job_fp).read_text(encoding="utf-8"))

    result = compute_match(profile, job, run_id, profile_fp, job_fp)
    out_path = write_match_result(result)

    log_event(logger, "match_completed", run_id, score=result.score, path=str(out_path))
    return {
        "status": "ok",
        "path": str(out_path),
        "score": result.score,
        "run_id": run_id,
        "overlap": result.overlap_skills,
        "missing": result.missing_skills,
    }


# ------------------------------------------------------------------------------
# P5 — Ranking
# ------------------------------------------------------------------------------
@app.post("/rank/run")
def run_ranking(top_n: int = 3, recent_jobs: int = 20):
    run_id = new_run_id()

    profile_fp = latest_file("outputs/profile/profile_v1_*.json")
    if not profile_fp:
        return {"status": "error", "message": "No profile artifacts found. Run P2 first.", "run_id": run_id}

    try:
        job_files = sorted(glob.glob("outputs/jobs/job_post_v1_*.json"))
        if recent_jobs > 0 and len(job_files) > recent_jobs:
            job_files = job_files[-recent_jobs:]

        shortlist = rank_all_jobs(
            profile_path=profile_fp,
            top_n=top_n,
            run_id=run_id,
            job_paths=job_files,
        )
        out_path = write_shortlist(shortlist)
        log_event(logger, "ranking_completed", run_id, top_n=top_n, path=str(out_path))
        return {
            "status": "ok",
            "path": str(out_path),
            "run_id": run_id,
            "top_n": top_n,
            "items": [i.model_dump() for i in shortlist.items],
        }
    except Exception as e:
        log_exception(logger, "ranking_failed", run_id, e)
        return {"status": "error", "message": str(e), "run_id": run_id}


# ------------------------------------------------------------------------------
# P6 — Generation (Top-1 from shortlist)
# ------------------------------------------------------------------------------
@app.post("/generate/package")
def generate_package():
    run_id = new_run_id()

    shortlist_fp = latest_file("outputs/ranking/shortlist_*.json") or latest_file("outputs/ranking/shortlist_v1_*.json")
    if not shortlist_fp:
        return {"status": "error", "message": "No shortlist found. Run P5 ranking first.", "run_id": run_id}

    shortlist = RankedShortlist.model_validate_json(Path(shortlist_fp).read_text(encoding="utf-8"))
    if not shortlist.items:
        return {"status": "error", "message": "Shortlist is empty.", "run_id": run_id}

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


# ------------------------------------------------------------------------------
# P7 — Guardrails
# ------------------------------------------------------------------------------
@app.post("/guardrails/validate")
def validate_latest_package():
    run_id = new_run_id()

    pkg_fp = latest_file("exports/packages/application_package_v1_*.json")
    profile_fp = latest_file("outputs/profile/profile_v1_*.json")

    if not pkg_fp or not profile_fp:
        return {"status": "error", "message": "Missing package or profile artifacts. Run P2 and P6 first.", "run_id": run_id}

    profile = EvidenceProfile.model_validate_json(Path(profile_fp).read_text(encoding="utf-8"))
    pkg = ApplicationPackage.model_validate_json(Path(pkg_fp).read_text(encoding="utf-8"))

    report: ValidationReport = validate_package_against_evidence(profile, pkg, run_id, pkg_fp)
    out_path = write_validation_report(report)

    if report.status == "blocked":
        log_event(logger, "guardrails_blocked", run_id, path=str(out_path))
        return {"status": "blocked", "path": str(out_path), "run_id": run_id, "findings": [f.model_dump() for f in report.findings]}

    log_event(logger, "guardrails_passed", run_id, path=str(out_path))
    return {"status": "pass", "path": str(out_path), "run_id": run_id}


# ------------------------------------------------------------------------------
# P8 — Export + Apply Tracking
# ------------------------------------------------------------------------------
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
        job_path=None,
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
    return rec


# ------------------------------------------------------------------------------
# P9 — Analytics
# ------------------------------------------------------------------------------
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


# ------------------------------------------------------------------------------
# P10 — Followups
# ------------------------------------------------------------------------------
@app.post("/followups/generate")
def followups_generate(followup_days: int = 3, stale_days: int = 14):
    queue = generate_next_actions(TRACKING_PATH, followup_days=followup_days, stale_days=stale_days)
    path = write_action_queue(queue)
    return {
        "status": "ok",
        "path": str(path),
        "queue": action_queue_to_dict(queue),
        "total": queue.total,
    }


@app.get("/followups/latest")
def followups_latest():
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


# ------------------------------------------------------------------------------
# P11 — Notifications / Drafts
# ------------------------------------------------------------------------------
@app.post("/notifications/generate")
def notifications_generate():
    followups_path = latest_action_queue_path()
    if not followups_path:
        return {
            "status": "error",
            "code": "not_found",
            "message": "No followups queue found. Run /followups/generate first.",
        }

    bundle = generate_drafts_from_followups(followups_path)
    out_path = write_drafts_bundle(bundle)

    return {
        "status": "ok",
        "path": out_path,
        "bundle": draft_bundle_to_dict(bundle),
        "total": bundle.total,
    }


@app.get("/notifications/latest")
def notifications_latest():
    path = latest_drafts_path()
    if not path:
        return {
            "status": "error",
            "code": "not_found",
            "message": "No drafts bundle found yet. Run /notifications/generate first.",
        }

    b = load_drafts_bundle(path)
    return {
        "status": "ok",
        "path": path,
        "bundle": draft_bundle_to_dict(b),
        "total": b.total,
    }


# ------------------------------------------------------------------------------
# P12 — Orchestrator (P6 → P11)
# ------------------------------------------------------------------------------
@app.post("/orchestrator/run")
def orchestrator_run(followup_days: int = 3, stale_days: int = 14):
    return run_p6_to_p11(followup_days=followup_days, stale_days=stale_days)


#P14 - Agentic Orchestrator (P6 -> P11 with state + tool registry)
class P14RunRequest(BaseModel):
    run_id: str
    profile_path: str
    job_path: str
    overlap_skills: list[str] = []
    followup_days: int = 3
    stale_days: int = 14
    tracking_path: str = "outputs/apply_tracking/applications_v1.jsonl"

@app.post("/runs/execute_plan")
def runs_execute_plan(req: P14RunRequest):
    return run_plan_p6_to_p11(
        run_id=req.run_id,
        profile_path=req.profile_path,
        job_path=req.job_path,
        overlap_skills=req.overlap_skills,
        followup_days=req.followup_days,
        stale_days=req.stale_days,
        tracking_path=req.tracking_path,
    )


class P17GroundingRequest(BaseModel):
    resume_text: str
    job_text: str
    candidate_name: str | None = None


@app.post("/p17/grounding")
def p17_grounding(req: P17GroundingRequest):
    run_id = new_run_id()
    profile = build_profile_from_text(req.resume_text, candidate_name=req.candidate_name)
    job = build_jobpost_from_text(req.job_text)

    required_skills = job.keywords or []
    retrieval = retrieve_chunks_for_skills(profile, required_skills)

    skill_to_chunk_ids: dict[str, list[str]] = {}
    for c in retrieval.chunks:
        for tag in c.tags:
            skill_to_chunk_ids.setdefault(tag.lower(), []).append(c.chunk_id)

    grounded_pkg: ApplicationPackageV2 = build_grounded_package_v2(
        profile=profile,
        job=job,
        run_id=run_id,
        profile_path="inline:resume_text",
        job_path="inline:job_text",
        overlap_skills=required_skills,
        skill_to_chunk_ids=skill_to_chunk_ids,
    )
    out_path = write_application_package_v2(grounded_pkg)
    return {
        "status": "ok",
        "run_id": run_id,
        "path": str(out_path),
        "required_skills": required_skills,
        "retrieved_chunks": [c.model_dump() for c in retrieval.chunks],
        "package": grounded_pkg.model_dump(),
    }



class P18ValidationRequest(BaseModel):
    package_path: str | None = None


@app.post("/p18/guardrails_v2")
def p18_guardrails_v2(req: P18ValidationRequest):
    run_id = new_run_id()
    package_path = req.package_path or latest_file("exports/packages/application_package_v2_*.json")
    if not package_path:
        raise HTTPException(status_code=404, detail="No v2 package found. Run /p17/grounding first.")

    pkg = ApplicationPackageV2.model_validate_json(Path(package_path).read_text(encoding="utf-8"))
    missing_citations = [b.text for b in pkg.bullets if not b.evidence_chunk_ids]

    status = "pass"
    findings: list[ValidationFinding] = []
    if pkg.citations_required and (not pkg.citations_complete or missing_citations):
        status = "blocked"
        findings.append(
            ValidationFinding(
                severity="block",
                rule_id="GRV2_001",
                message="Every generated bullet must include evidence_chunk_ids for P18.",
                unsupported_terms=missing_citations[:5],
                evidence_reference={"missing_bullets": len(missing_citations)},
            )
        )

    report = {
        "version": "v2",
        "run_id": run_id,
        "status": status,
        "package_path": package_path,
        "citations_required": pkg.citations_required,
        "citations_complete": pkg.citations_complete,
        "missing_citations_count": len(missing_citations),
        "findings": [f.model_dump() for f in findings],
    }
    out_dir = Path("outputs/guardrails")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"validation_report_v2_{run_id}.json"
    out_path.write_text(__import__("json").dumps(report, indent=2), encoding="utf-8")
    report["path"] = str(out_path)
    return report


class P19StateRequest(BaseModel):
    env: str | None = None
    mode: str = "agentic"


@app.post("/p19/state/new")
def p19_state_new(req: P19StateRequest):
    state = OrchestratorState.new(mode=req.mode, env=req.env or settings.env)
    fp = write_state(state)
    return {"status": "ok", "phase": "P19", "run_id": state.run_id, "state_path": str(fp), "state": state.model_dump()}


@app.get("/p19/state/latest")
def p19_state_latest():
    state_fp = latest_file("outputs/runs/state_*.json")
    if not state_fp:
        return {"status": "idle", "message": "No P19 state yet. Run /p19/state/new."}
    raw = Path(state_fp).read_text(encoding="utf-8")
    return {"status": "ok", "path": state_fp, "state": OrchestratorState.model_validate_json(raw).model_dump()}




@app.get("/phase3/readiness")
def phase3_readiness():
    """Return Phase 3 readiness summary and key-presence checks (boolean only)."""
    return {
        "status": "ok",
        "phase": "phase3_bootstrap",
        "checks": {
            "openai_api_key_present": bool(settings.openai_api_key),
            "huggingface_api_key_present": bool(settings.huggingface_api_key),
            "tavily_api_key_present": bool(settings.tavily_api_key),
            "serper_api_key_present": bool(settings.serper_api_key),
        },
        "steps": PHASE3_STEPS,
    }


@app.post("/p20/contracts/validate")
def p20_contracts_validate(payload: dict):
    """P20: validate typed agent contracts before orchestration."""
    result = validate_contract(payload)
    return result.model_dump()


@app.post("/p21/langgraph/dry_run")
def p21_langgraph_dry_run(payload: dict):
    """P21 bootstrap: run contract-validated dry-run and write phase3 artifact."""
    validation = validate_contract(payload)
    if validation.status != "ok":
        return {"status": "error", "errors": validation.errors}

    req = AgentTaskInput.model_validate(validation.normalized)
    out = dry_run_agent_step(req)
    return {"status": "ok", "result": out.model_dump()}


@app.post("/p21/langgraph/run")
def p21_langgraph_run(payload: dict):
    """P21 implementation: execute deterministic LangGraph node pipeline (match->rank->generate->guardrails)."""
    run_id = str(payload.get("run_id") or new_run_id())
    result = run_langgraph_pipeline(
        run_id=run_id,
        profile_path=payload.get("profile_path"),
        job_path=payload.get("job_path"),
        top_n=int(payload.get("top_n", 3)),
    )
    errors = result.get("errors") or []
    return {
        "status": "error" if errors else "ok",
        "run_id": run_id,
        "result": result,
        "errors": errors,
    }




@app.post("/p22/approval/decision")
def p22_approval_decision(payload: dict):
    run_id = str(payload.get("run_id") or new_run_id())
    approved = bool(payload.get("approved", False))
    reviewer = str(payload.get("reviewer") or "human")
    notes = payload.get("notes")
    result = write_p22_approval_decision(run_id=run_id, approved=approved, reviewer=reviewer, notes=notes)
    return {"status": "ok", "result": result}


@app.get("/p22/approval/latest")
def p22_approval_latest(run_id: str):
    return latest_p22_approval(run_id)


@app.post("/p23/memory/upsert")
def p23_memory_upsert_endpoint(payload: dict):
    return p23_memory_upsert(
        run_id=str(payload.get("run_id") or new_run_id()),
        namespace=str(payload.get("namespace") or "default"),
        key=str(payload.get("key") or "entry"),
        value=payload.get("value"),
    )


@app.get("/p23/memory/get")
def p23_memory_get_endpoint(run_id: str, namespace: str, key: str):
    return p23_memory_get(run_id=run_id, namespace=namespace, key=key)


@app.post("/p24/evaluator/run")
def p24_evaluator_run(payload: dict):
    run_id = str(payload.get("run_id") or new_run_id())
    return p24_evaluate_run(run_id)


@app.post("/agents/parser/extract")
def agent_parser_extract(payload: dict):
    return parser_extract(payload)


@app.post("/agents/vision/ocr")
def agent_vision_ocr(payload: dict):
    return vision_ocr(payload)


@app.post("/agents/connector/ingest")
def agent_connector_ingest(payload: dict):
    return connector_ingest(payload)



@app.post("/p24/evaluator/run_v2")
def p24_evaluator_run_v2(payload: dict):
    run_id = str(payload.get("run_id") or new_run_id())
    w = payload.get("weights") or {}
    weights = EvalWeights(
        match_quality=int(w.get("match_quality", 30)),
        guardrails_quality=int(w.get("guardrails_quality", 25)),
        approval_quality=int(w.get("approval_quality", 20)),
        package_quality=int(w.get("package_quality", 15)),
        pipeline_reliability=int(w.get("pipeline_reliability", 10)),
    )
    return evaluate_run_v2(run_id=run_id, weights=weights)


@app.get("/p24/evaluator/latest")
def p24_evaluator_latest(run_id: str):
    return latest_eval_v2(run_id)






if _MULTIPART_AVAILABLE:
    @app.post("/p25/automation/run_upload")
    def p25_automation_run_upload(
        resume_file: UploadFile = File(...),
        job_file: UploadFile = File(...),
        candidate_name: str | None = Form(default=None),
        run_id: str | None = Form(default=None),
        top_n: int = Form(default=3),
    ):
        resume_text = _extract_upload_text(resume_file)
        job_text = _extract_upload_text(job_file)
        if not resume_text.strip():
            return {"status": "error", "message": "Unable to extract readable text from resume upload. Please upload selectable-text PDF/DOCX or paste resume text."}
        if not job_text.strip():
            return {"status": "error", "message": "Unable to extract readable text from job upload. Please upload selectable-text PDF/DOCX or paste job text."}
        payload = {
            "run_id": run_id,
            "candidate_name": candidate_name,
            "top_n": top_n,
            "resume": {"source_type": "inline", "text": resume_text},
            "jobs": {"job_texts": [job_text]},
        }
        return p25_automation_run(payload)

    @app.post("/p25/automation/run_upload_auto")
    def p25_automation_run_upload_auto(
        resume_file: UploadFile = File(...),
        candidate_name: str | None = Form(default=None),
        run_id: str | None = Form(default=None),
        top_n: int = Form(default=5),
        roles_csv: str = Form(default="ML Engineer,Backend Engineer,GenAI Engineer"),
        location: str = Form(default="USA"),
        daily_limit: int = Form(default=20),
        private_mode: bool = Form(default=True),
        recent_hours: int = Form(default=36),
    ):
        resume_text = _extract_upload_text(resume_file)
        if not resume_text.strip():
            return {"status": "error", "message": "Unable to extract readable text from resume upload. Please upload selectable-text PDF/DOCX or paste resume text."}
        roles = [x.strip() for x in roles_csv.split(",") if x.strip()]
        payload = {
            "run_id": run_id,
            "candidate_name": candidate_name,
            "top_n": top_n,
            "privacy": {"private_mode": bool(private_mode)},
            "resume": {"source_type": "inline", "text": resume_text},
            "jobs": {
                "auto_discover": True,
                "daily_limit": int(daily_limit),
                "max_per_source": 2,
                "preferences": {"roles": roles, "location": location, "recent_hours": int(recent_hours)},
            },
        }
        return p25_automation_run(payload)
else:
    @app.post("/p25/automation/run_upload")
    def p25_automation_run_upload_unavailable():
        return {
            "status": "error",
            "message": "python-multipart is not installed. Install with: pip install python-multipart",
        }

    @app.post("/p25/automation/run_upload_auto")
    def p25_automation_run_upload_auto_unavailable():
        return {
            "status": "error",
            "message": "python-multipart is not installed. Install with: pip install python-multipart",
        }

@app.post("/p25/automation/run")
def p25_automation_run_endpoint(payload: dict):
    return p25_automation_run(payload)


@app.get("/p25/automation/trace/latest")
def p25_automation_trace_latest(run_id: str | None = None):
    return latest_p25_trace(run_id)

@app.get("/p25/system/health")
def p25_system_health():
    return run_system_health_checks()


@app.get("/p25/automation/layers/latest")
def p25_automation_layers_latest(run_id: str | None = None):
    """Return a layer-by-layer status view for the latest P25 trace artifact."""
    trace_resp = latest_p25_trace(run_id)
    if trace_resp.get("status") != "ok":
        return trace_resp

    trace = trace_resp.get("trace", {})
    layers = trace.get("layers", {})
    ordered = [
        "L1_intake_bootstrap",
        "L2_parsing",
        "L3_jobs",
        "L4_matching",
        "L5_ranking",
        "L6_generation",
        "L7_guardrails",
        "L8_summary",
        "L9_vector_indexing",
        "L10_hitl_decision",
    ]

    rows: list[dict] = []
    for layer in ordered:
        if layer in {"L1_intake_bootstrap", "L9_vector_indexing", "L10_hitl_decision"}:
            rows.append({"layer": layer, "status": "derived", "details": "Available from run output payload."})
            continue
        node = layers.get(layer, {})
        rows.append(
            {
                "layer": layer,
                "status": "ok" if node else "missing",
                "agent": node.get("agent"),
                "input": node.get("input", {}),
                "output": node.get("output", {}),
                "next_layer": node.get("next_layer"),
            }
        )

    return {
        "status": "ok",
        "run_id": trace.get("run_id"),
        "trace_path": trace_resp.get("path"),
        "layers": rows,
    }


@app.get("/system/architecture/map")
def system_architecture_map():
    """Expose where major agents, orchestration, retrieval, and persistence components live."""
    return {
        "status": "ok",
        "layers": {
            "L1_intake": {"api": "apps/api/main.py::/intake,/intake/bootstrap", "schema": "src/careeros/intake/schema.py", "service": "src/careeros/intake/service.py"},
            "L2_resume_profile": {"api": "apps/api/main.py::/profile", "agent": "src/careeros/phase3/next_steps.py::parser_extract", "service": "src/careeros/parsing/service.py"},
            "L3_jobs_ingestion": {"api": "apps/api/main.py::/jobs/ingest,/jobs/discover_ingest", "discovery": "src/careeros/integrations/job_boards/sources.py", "agent": "src/careeros/phase3/next_steps.py::connector_ingest"},
            "L4_matching": {"api": "apps/api/main.py::/match/run", "service": "src/careeros/matching/service.py"},
            "L5_ranking": {"api": "apps/api/main.py::/rank/run", "service": "src/careeros/ranking/service.py"},
            "L6_generation": {"api": "apps/api/main.py::/generate/package", "service": "src/careeros/generation/service.py"},
            "L7_guardrails": {"api": "apps/api/main.py::/guardrails/validate", "service": "src/careeros/guardrails/service.py"},
            "L8_summary": {"router": "src/careeros/orchestration/router.py::generate_summary_with_fallback", "entry": "src/careeros/phase3/next_steps.py::_ollama_summary"},
            "L9_vectors_rag": {"store": "src/careeros/evidence/vector_store.py", "indexing": "src/careeros/phase3/next_steps.py::p25_automation_run", "retrieval": "src/careeros/evidence/service.py"},
            "L10_hitl": {"agent": "src/careeros/phase3/next_steps.py::_hitl_decision", "approval_api": "apps/api/main.py::/p22/approval/decision"},
        },
        "orchestration": {
            "p25": "src/careeros/phase3/next_steps.py::p25_automation_run",
            "langgraph": "src/careeros/phase3/langgraph_flow.py",
            "p14_agentic": "src/careeros/agentic/p14_orchestrator.py",
        },
        "ui": "apps/ui/Home.py",
        "artifact_roots": ["outputs/", "exports/", "data/"],
    }


@app.post("/artifacts/share/latest")
def artifacts_share_latest(payload: dict | None = None):
    """Upload latest key artifacts to transfer.sh (ephemeral sharing) when enabled."""
    payload = payload or {}
    if str(os.getenv("ENABLE_TRANSFER_SH", "false")).lower() not in {"1", "true", "yes"}:
        return {
            "status": "error",
            "message": "Cloud artifact sharing is disabled. Set ENABLE_TRANSFER_SH=true to enable transfer.sh upload.",
        }
    patterns = payload.get("patterns") or [
        "outputs/phase3/p25_runs/p25_trace_*.json",
        "outputs/ranking/shortlist_*.json",
        "outputs/guardrails/validation_report_*.json",
        "outputs/profile/profile_*.json",
    ]
    links: list[dict] = []
    errors: list[str] = []
    for pattern in patterns:
        fp = latest_file(pattern)
        if not fp:
            continue
        try:
            with open(fp, "rb") as f:
                r = httpx.put(f"https://transfer.sh/{Path(fp).name}", content=f.read(), timeout=45)
            if r.status_code in (200, 201):
                links.append({"file": fp, "url": r.text.strip()})
            else:
                errors.append(f"{fp}: http_{r.status_code}")
        except Exception as e:
            errors.append(f"{fp}: {e}")
    return {"status": "ok" if links else "degraded", "links": links, "errors": errors}


SAFE_ARTIFACT_ROOTS = [
    Path("outputs").resolve(),
    Path("exports").resolve(),
    Path("data").resolve(),
]


def _safe_artifact_path(path: str) -> Path:
    candidate = Path(path).expanduser().resolve()
    for root in SAFE_ARTIFACT_ROOTS:
        if root in candidate.parents or candidate == root:
            return candidate
    raise HTTPException(status_code=400, detail="Path is outside allowed artifact roots")


@app.get("/artifacts/open")
def artifacts_open(path: str):
    fp = _safe_artifact_path(path)
    if not fp.exists() or not fp.is_file():
        raise HTTPException(status_code=404, detail="Artifact file not found")
    return FileResponse(fp)


@app.get("/artifacts/read")
def artifacts_read(path: str):
    fp = _safe_artifact_path(path)
    if not fp.exists() or not fp.is_file():
        raise HTTPException(status_code=404, detail="Artifact file not found")
    if fp.suffix.lower() in {".json", ".md", ".txt", ".log", ".jsonl"}:
        return {"status": "ok", "path": str(fp), "content": fp.read_text(encoding="utf-8", errors="ignore")}
    return {"status": "ok", "path": str(fp), "message": "Use /artifacts/open for binary formats"}


@app.post("/feedback/submit")
def feedback_submit(payload: dict):
    return append_feedback(payload)


@app.get("/feedback/list")
def feedback_list(limit: int = 100):
    return list_feedback(limit=limit)


@app.post("/feedback/employer_signal")
def feedback_employer_signal(payload: dict):
    return append_employer_signal(payload)


@app.get("/phases/status")
def phases_status():
    phase_status = {
        **{f"P{i}": "ready" for i in range(1, 18)},
        "P18": "ready",
        "P19": "ready",
        "P20": "ready",
        "P21": "ready",
        "P22": "ready",
        "P23": "ready",
        "P24": "ready",
        "P25": "ready",
    }
    return {
        "status": "ok",
        "phases": [
            {"phase": p, "status": st, "available": st == "ready"} for p, st in phase_status.items()
        ],
        "next_focus": "P26 (beta hardening + feedback loop)",
    }


#p15
app.include_router(orchestrator.router, tags=["P15-Human-Gate"])
