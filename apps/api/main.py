from __future__ import annotations

import glob
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


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


# ------------------------------------------------------------------------------
# App boot
# ------------------------------------------------------------------------------
settings = load_settings()
logger = get_logger()

app = FastAPI(title="CareerOS API", version="0.1.0")


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
def run_ranking(top_n: int = 3):
    run_id = new_run_id()

    profile_fp = latest_file("outputs/profile/profile_v1_*.json")
    if not profile_fp:
        return {"status": "error", "message": "No profile artifacts found. Run P2 first.", "run_id": run_id}

    try:
        shortlist = rank_all_jobs(profile_path=profile_fp, top_n=top_n, run_id=run_id)
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


@app.get("/phases/status")
def phases_status():
    phase_status = {
        **{f"P{i}": "ready" for i in range(1, 18)},
        "P18": "ready",
        "P19": "ready",
        "P20": "ready",
        "P21": "ready",
        "P22": "planned",
        "P23": "planned",
        "P24": "planned",
    }
    return {
        "status": "ok",
        "phases": [
            {"phase": p, "status": st, "available": st == "ready"} for p, st in phase_status.items()
        ],
        "next_focus": "P22",
    }


#p15
app.include_router(orchestrator.router, tags=["P15-Human-Gate"])
