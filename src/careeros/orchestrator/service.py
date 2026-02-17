from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from careeros.parsing.schema import EvidenceProfile
from careeros.jobs.schema import JobPost

# P2/P3: you already have writers; we only need "latest" helpers here
from careeros.parsing.service import latest_profile_path

# P6
from careeros.generation.service import build_package, write_application_package

# P7
from careeros.guardrails.service import validate_package_against_evidence, write_validation_report

# P8
from careeros.export.service import export_latest_validated_package
from careeros.tracking.service import create_application_record, write_application_record

# P10
from careeros.followups.service import generate_next_actions, write_action_queue

# P11
from careeros.notifications.service import generate_drafts_from_followups, write_drafts_bundle


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _latest_file(pattern: str) -> Optional[str]:
    files = sorted(Path(".").glob(pattern))
    return str(files[-1]) if files else None


def _write_json(path: str | Path, obj: Any) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    return str(p)


def _json_safe(obj: Any) -> Any:
    """Recursively convert Path objects to str so JSON + FastAPI responses never crash."""
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(x) for x in obj]
    return obj


def _finalize_and_write(run_id: str, now: datetime, out: Dict[str, Any]) -> Dict[str, Any]:
    """
    IMPORTANT:
    - First make it JSON-safe (convert Path -> str)
    - Then write JSON (so _write_json never crashes)
    - Then return JSON-safe output (so FastAPI never crashes)
    """
    safe = _json_safe(out)
    out_path = _write_json(f"outputs/orchestrator/orchestrator_run_v1_{now.strftime('%Y%m%d_%H%M%S')}.json", safe)
    safe["path"] = out_path
    return safe


def latest_shortlist_path() -> Optional[str]:
    # Your ranking writes shortlist artifacts here
    return _latest_file("outputs/ranking/shortlist_*.json")


def load_shortlist_dict(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8"))


def load_profile_json(path: str | Path) -> EvidenceProfile:
    p = Path(path)
    d = json.loads(p.read_text(encoding="utf-8"))
    return EvidenceProfile.model_validate(d)


def load_job_post_json(path: str | Path) -> JobPost:
    p = Path(path)
    d = json.loads(p.read_text(encoding="utf-8"))
    return JobPost.model_validate(d)


@dataclass
class StepResult:
    step_id: str
    status: str  # ok | blocked | error | skipped
    message: str
    artifact_path: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


def run_p6_to_p11(*, followup_days: int = 3, stale_days: int = 14) -> Dict[str, Any]:
    """
    Uses latest artifacts (profile + shortlist) like the UI flow.
    Runs: P6 -> P7 -> P8 -> P10 -> P11
    """
    run_id = uuid.uuid4().hex
    now = _utc_now()
    steps: List[StepResult] = []
    outputs: Dict[str, Any] = {}

    prof_path = latest_profile_path()
    short_path = latest_shortlist_path()

    if not prof_path or not short_path:
        out = {
            "version": "v1",
            "run_id": run_id,
            "created_at_utc": _iso(now),
            "final_status": "error",
            "message": "Missing latest profile or shortlist. Run P2 (profile) and P5 (ranking) first.",
            "steps": [],
            "outputs": {"profile_path": prof_path, "shortlist_path": short_path},
        }
        return _finalize_and_write(run_id, now, out)

    shortlist = load_shortlist_dict(short_path)
    items = shortlist.get("items") or shortlist.get("shortlist") or []
    if not items:
        out = {
            "version": "v1",
            "run_id": run_id,
            "created_at_utc": _iso(now),
            "final_status": "error",
            "message": "Shortlist has no items.",
            "steps": [],
            "outputs": {"profile_path": prof_path, "shortlist_path": short_path},
        }
        return _finalize_and_write(run_id, now, out)

    top = items[0]
    job_path = top.get("job_path")
    overlap_skills = top.get("overlap_skills", []) or top.get("overlap", []) or []

    return run_p6_to_p11_from_inputs(
        profile_path=prof_path,
        job_path=job_path,
        overlap_skills=overlap_skills,
        followup_days=followup_days,
        stale_days=stale_days,
        shortlist_path=short_path,
        run_id=run_id,
    )


def run_p6_to_p11_from_inputs(
    *,
    profile_path: Optional[str],
    job_path: Optional[str],
    overlap_skills: Optional[List[str]] = None,
    followup_days: int = 3,
    stale_days: int = 14,
    tracking_path: str = "outputs/apply_tracking/applications_v1.jsonl",
    shortlist_path: Optional[str] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    P12 entrypoint: run orchestration from explicit inputs.
    If profile_path/job_path are missing, it falls back safely to "latest" logic.
    """
    rid = run_id or uuid.uuid4().hex
    now = _utc_now()
    steps: List[StepResult] = []
    outputs: Dict[str, Any] = {}

    # Fallbacks
    prof_path = (profile_path or "").strip() or latest_profile_path()
    if not prof_path:
        out = {
            "version": "v1",
            "run_id": rid,
            "created_at_utc": _iso(now),
            "final_status": "error",
            "message": "No profile_path provided and no latest profile found. Run P2 first.",
            "steps": [],
            "outputs": {"profile_path": prof_path},
        }
        return _finalize_and_write(rid, now, out)

    jpath = (job_path or "").strip() if job_path else ""
    if not jpath:
        # If job_path not provided, try from latest shortlist
        spath = shortlist_path or latest_shortlist_path()
        if spath:
            s = load_shortlist_dict(spath)
            items = s.get("items") or s.get("shortlist") or []
            if items:
                top = items[0]
                jpath = top.get("job_path") or ""
                overlap_skills = overlap_skills or top.get("overlap_skills", []) or top.get("overlap", []) or []
                outputs["shortlist_path"] = spath

    if not jpath:
        out = {
            "version": "v1",
            "run_id": rid,
            "created_at_utc": _iso(now),
            "final_status": "error",
            "message": "No job_path provided and no latest shortlist job_path found. Run P5 first or pass job_path.",
            "steps": [],
            "outputs": {"profile_path": prof_path, "job_path": jpath},
        }
        return _finalize_and_write(rid, now, out)

    overlap = overlap_skills or []

    outputs["profile_path"] = prof_path
    outputs["job_path"] = jpath
    outputs["overlap_skills"] = overlap

    try:
        # -------------------------
        # P6: Generation
        # -------------------------
        profile = load_profile_json(prof_path)
        job = load_job_post_json(jpath)

        pkg = build_package(
            profile,
            job,
            run_id=rid,
            profile_path=prof_path,
            job_path=jpath,
            overlap_skills=overlap,
        )
        pkg_path = write_application_package(pkg)
        pkg_path = str(pkg_path)  # IMPORTANT: normalize Path -> str
        outputs["package_path"] = pkg_path
        steps.append(StepResult("P6_generation", "ok", "Generated application package", pkg_path))

        # -------------------------
        # P7: Guardrails
        # -------------------------
        report = validate_package_against_evidence(profile, pkg, run_id=run_id, package_path=pkg_path)
        rep_path = write_validation_report(report)
        rep_path = str(rep_path)
        outputs["validation_report_path"] = rep_path

        if report.status == "blocked":
            unsupported = []
            if getattr(report, "findings", None):
                f0 = report.findings[0]
                unsupported = getattr(f0, "unsupported_terms", []) or []
            steps.append(
                StepResult(
                    "P7_guardrails",
                    "blocked",
                    "Guardrails blocked the package",
                    rep_path,
                    meta={"unsupported_terms": unsupported},
                )
            )

            out = {
                "version": "v1",
                "run_id": rid,
                "created_at_utc": _iso(now),
                "final_status": "blocked",
                "blocked_at": "P7",
                "steps": [asdict(s) for s in steps],
                "outputs": outputs,
            }
            return _finalize_and_write(rid, now, out)

        steps.append(StepResult("P7_guardrails", "ok", "Guardrails passed", rep_path))

        # -------------------------
        # P8: Export + Tracking
        # -------------------------
        export_result = export_latest_validated_package()
        outputs["submission_dir"] = export_result.get("submission_dir")
        outputs["export_docx_path"] = export_result.get("docx_path")
        outputs["export_pdf_path"] = export_result.get("pdf_path")
        steps.append(
            StepResult(
                "P8_export",
                "ok",
                "Exported package",
                export_result.get("submission_dir"),
                meta=_json_safe(export_result),
            )
        )

        rec = create_application_record(
            run_id=rid,
            job_path=jpath,
            package_path=pkg_path,
            validation_report_path=rep_path,
            export_docx_path=export_result.get("docx_path"),
            export_pdf_path=export_result.get("pdf_path"),
            status="exported",
        )
        tracking_written = write_application_record(rec, tracking_path=tracking_path)
        outputs["tracking_path"] = tracking_written
        outputs["application_id"] = rec.application_id
        steps.append(
            StepResult(
                "P8_tracking",
                "ok",
                "Tracking record created",
                tracking_written,
                meta={"application_id": rec.application_id},
            )
        )

        # -------------------------
        # P10: Followups
        # -------------------------
        q = generate_next_actions(tracking_path, followup_days=followup_days, stale_days=stale_days, run_id=rid)
        fq_path = write_action_queue(q)
        outputs["followups_path"] = fq_path
        outputs["followups_total"] = q.total
        steps.append(StepResult("P10_followups", "ok", "Generated next actions", fq_path, meta={"total": q.total}))

        # -------------------------
        # P11: Drafts
        # -------------------------
        bundle = generate_drafts_from_followups(str(fq_path), run_id=rid)
        dr_path = write_drafts_bundle(bundle)
        outputs["drafts_path"] = dr_path
        outputs["drafts_total"] = bundle.total
        steps.append(StepResult("P11_notifications", "ok", "Generated drafts", dr_path, meta={"total": bundle.total}))

        out = {
            "version": "v1",
            "run_id": rid,
            "created_at_utc": _iso(now),
            "final_status": "ok",
            "steps": [asdict(s) for s in steps],
            "outputs": outputs,
        }
        return _finalize_and_write(rid, now, out)

    except Exception as e:
        steps.append(StepResult("P12_orchestrator", "error", f"Unexpected error: {e}"))
        out = {
            "version": "v1",
            "run_id": rid,
            "created_at_utc": _iso(now),
            "final_status": "error",
            "steps": [asdict(s) for s in steps],
            "outputs": outputs,
        }
        return _finalize_and_write(rid, now, out)
