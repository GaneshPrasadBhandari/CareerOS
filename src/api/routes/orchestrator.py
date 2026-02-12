from __future__ import annotations

import glob
import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

# This line MUST exist for main.py to work
router = APIRouter()

STATE_FILE = "outputs/state/current_run.json"


def _latest_file(pattern: str) -> str | None:
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None


def _read_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _normalize_score_for_ui(raw: Any) -> float:
    try:
        val = float(raw)
    except Exception:
        return 0.0
    if val > 1.0:
        return round(val / 100.0, 4)
    return round(val, 4)


def _build_state_from_latest_match() -> dict[str, Any] | None:
    match_fp = _latest_file("outputs/matching/match_result_v1_*.json")
    if not match_fp:
        return None

    data = _read_json(match_fp)
    overlap = data.get("overlap_skills", []) or []
    top_match_id = Path(str(data.get("job_path", "unknown_job"))).stem
    return {
        "status": "pending",
        "top_match_id": top_match_id,
        "match_score": _normalize_score_for_ui(data.get("score", 0)),
        "overlap_skills": overlap,
        "source_match_path": match_fp,
        "is_approved": False,
        "user_feedback": "",
    }


@router.get("/orchestrator/current_state")
async def get_current_state(refresh: bool = Query(default=False)):
    """Reads state for UI. Can refresh from latest match artifact when requested."""
    if refresh:
        derived = _build_state_from_latest_match()
        if derived:
            Path(STATE_FILE).parent.mkdir(parents=True, exist_ok=True)
            Path(STATE_FILE).write_text(json.dumps(derived, indent=2), encoding="utf-8")
            return derived
        return {"status": "idle", "message": "No pending application state."}

    if os.path.exists(STATE_FILE):
        data = _read_json(STATE_FILE)
        data["match_score"] = _normalize_score_for_ui(data.get("match_score", 0))
        return data

    derived = _build_state_from_latest_match()
    if derived:
        Path(STATE_FILE).parent.mkdir(parents=True, exist_ok=True)
        Path(STATE_FILE).write_text(json.dumps(derived, indent=2), encoding="utf-8")
        return derived

    return {"status": "idle", "message": "No pending application state."}


@router.post("/orchestrator/reset")
async def reset_state():
    p = Path(STATE_FILE)
    if p.exists():
        p.unlink()
    return {"status": "ok", "message": "State reset."}


@router.post("/orchestrator/approve")
async def approve_match(payload: dict):
    if not os.path.exists(STATE_FILE):
        raise HTTPException(status_code=404, detail="State file missing")

    data = _read_json(STATE_FILE)
    data["is_approved"] = True
    data["user_feedback"] = payload.get("user_feedback", "")
    Path(STATE_FILE).write_text(json.dumps(data, indent=4), encoding="utf-8")
    return {"status": "approved"}


@router.post("/orchestrator/reject")
async def reject_match(payload: dict):
    if not os.path.exists(STATE_FILE):
        raise HTTPException(status_code=404, detail="State file missing")

    data = _read_json(STATE_FILE)
    data["is_approved"] = False
    data["is_rejected"] = True
    data["rejection_feedback"] = payload.get("feedback", "")
    Path(STATE_FILE).write_text(json.dumps(data, indent=4), encoding="utf-8")
    return {"status": "rejected"}
