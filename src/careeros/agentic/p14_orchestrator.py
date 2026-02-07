from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from careeros.agentic.state import OrchestratorState
from careeros.agentic.state_store import load_state, write_state

# Phase-1 bridge imports
from careeros.parsing.schema import EvidenceProfile
from careeros.jobs.schema import JobPost
from careeros.generation.service import build_package, write_application_package
from careeros.guardrails.service import validate_package_against_evidence, write_validation_report
from careeros.export.service import export_latest_validated_package
from careeros.tracking.service import append_jsonl, _utc_now
from careeros.tracking.schema import ApplicationRecord
from careeros.followups.service import generate_next_actions, write_action_queue
from careeros.notifications.service import generate_drafts_from_followups, write_drafts_bundle


def _utc_now_dt() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: str) -> Dict[str, Any]:
    import json
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_profile(profile_path: str) -> EvidenceProfile:
    return EvidenceProfile.model_validate(_read_json(profile_path))


def _load_job(job_path: str) -> JobPost:
    return JobPost.model_validate(_read_json(job_path))


@dataclass
class StepResult:
    step_id: str
    status: str
    message: str
    artifact_path: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    return obj


def run_plan_p6_to_p11(
    *,
    profile_path: str,
    job_path: str,
    overlap_skills: Optional[List[str]] = None,
    followup_days: int = 3,
    stale_days: int = 14,
    run_id: Optional[str] = None,
    state_path_or_run_id: Optional[str] = None,
    tracking_ledger_path: str = "outputs/apply_tracking/applications_v1.jsonl",
) -> Dict[str, Any]:
    rid = run_id or uuid.uuid4().hex
    now = _utc_now_dt()
    steps: List[StepResult] = []
    outputs: Dict[str, Any] = {}

    # load or create state
    if state_path_or_run_id:
        try:
            state = load_state(state_path_or_run_id)
        except FileNotFoundError:
            state = OrchestratorState.new(run_id=rid)
    else:
        state = OrchestratorState.new(run_id=rid)

    # ✅ input validation (tests expect status key)
    if not Path(profile_path).exists() or not Path(job_path).exists():
        state.artifacts.profile_path = profile_path
        state.artifacts.job_path = job_path
        write_state(state)

        steps.append(
            StepResult(
                step_id="P14_input_validation",
                status="error",
                message="profile_path or job_path not found",
                meta={"profile_path": profile_path, "job_path": job_path},
            )
        )
        out = {
            "version": "v1",
            "status": "error",
            "run_id": rid,
            "created_at_utc": _iso(now),
            "final_status": "error",
            "steps": [asdict(s) for s in steps],
            "outputs": outputs,
        }
        return _json_safe(out)

    try:
        overlap_skills = overlap_skills or []
        state.artifacts.profile_path = profile_path
        state.artifacts.job_path = job_path
        state.artifacts.overlap_skills = overlap_skills

        # -------------------------
        # P6
        # -------------------------
        profile = _load_profile(profile_path)
        job = _load_job(job_path)

        pkg = build_package(
            profile=profile,
            job=job,
            run_id=rid,
            profile_path=profile_path,
            job_path=job_path,
            overlap_skills=overlap_skills,
        )
        pkg_path = write_application_package(pkg)
        state.artifacts.package_path = str(pkg_path)
        outputs["package_path"] = str(pkg_path)
        steps.append(StepResult("P6_generation", "ok", "Generated application package", str(pkg_path)))

        # -------------------------
        # P7
        # -------------------------
        rep = validate_package_against_evidence(profile, pkg, run_id=rid, package_path=str(pkg_path))
        rep_path = write_validation_report(rep)
        state.artifacts.validation_report_path = str(rep_path)
        outputs["validation_report_path"] = str(rep_path)

        if rep.status == "blocked":
            steps.append(StepResult("P7_guardrails", "blocked", "Guardrails blocked", str(rep_path)))
            write_state(state)
            out = {
                "version": "v1",
                "status": "blocked",
                "run_id": rid,
                "created_at_utc": _iso(now),
                "final_status": "blocked",
                "blocked_at": "P7",
                "steps": [asdict(s) for s in steps],
                "outputs": outputs,
            }
            return _json_safe(out)

        steps.append(StepResult("P7_guardrails", "ok", "Guardrails passed", str(rep_path)))

        # -------------------------
        # P8 Export
        # -------------------------
        export_result = export_latest_validated_package()
        state.artifacts.export_docx_path = export_result.get("docx_path")
        state.artifacts.export_pdf_path = export_result.get("pdf_path")
        outputs["export_docx_path"] = export_result.get("docx_path")
        outputs["export_pdf_path"] = export_result.get("pdf_path")

        steps.append(StepResult("P8_export", "ok", "Exported package", export_result.get("docx_path"), meta=export_result))

        # Tracking
        app_id = export_result.get("application_id") or f"app_{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        rec = ApplicationRecord(
            version="v1",
            application_id=app_id,
            run_id=rid,
            job_path=job_path,
            package_path=str(pkg_path),
            validation_report_path=str(rep_path),
            export_docx_path=export_result.get("docx_path"),
            export_pdf_path=export_result.get("pdf_path"),
            status="exported",
            created_at_utc=_utc_now(),
            updated_at_utc=_utc_now(),
        )
        append_jsonl(tracking_ledger_path, rec)
        state.artifacts.tracking_path = tracking_ledger_path
        state.artifacts.application_id = rec.application_id
        outputs["tracking_path"] = tracking_ledger_path
        outputs["application_id"] = rec.application_id
        steps.append(StepResult("P8_tracking", "ok", "Tracking record created", tracking_ledger_path, meta={"application_id": rec.application_id}))

        # -------------------------
        # P10 Followups
        # -------------------------
        q = generate_next_actions(tracking_ledger_path, followup_days=followup_days, stale_days=stale_days, run_id=rid)
        fq_path = write_action_queue(q)
        state.artifacts.followups_path = str(fq_path)
        outputs["followups_path"] = str(fq_path)
        outputs["followups_total"] = q.total
        steps.append(StepResult("P10_followups", "ok", "Generated next actions", str(fq_path), meta={"total": q.total}))

        # -------------------------
        # P11 Drafts
        # -------------------------
        bundle = generate_drafts_from_followups(str(fq_path), run_id=rid)
        dr_path = write_drafts_bundle(bundle)
        state.artifacts.drafts_path = str(dr_path)
        outputs["drafts_path"] = str(dr_path)
        outputs["drafts_total"] = bundle.total
        steps.append(StepResult("P11_notifications", "ok", "Generated drafts", str(dr_path), meta={"total": bundle.total}))

        # persist state
        outputs["state_path"] = write_state(state)

        out = {
            "version": "v1",
            "status": "ok",
            "run_id": rid,
            "created_at_utc": _iso(now),
            "final_status": "ok",
            "steps": [asdict(s) for s in steps],
            "outputs": outputs,
        }
        return _json_safe(out)

    except Exception as e:
        steps.append(StepResult("P14_orchestrator", "error", f"Unexpected error: {e}"))
        try:
            write_state(state)
        except Exception:
            pass
        out = {
            "version": "v1",
            "status": "error",
            "run_id": rid,
            "created_at_utc": _iso(now),
            "final_status": "error",
            "steps": [asdict(s) for s in steps],
            "outputs": outputs,
        }
        return _json_safe(out)
