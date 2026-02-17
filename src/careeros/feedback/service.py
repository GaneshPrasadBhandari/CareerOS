from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FEEDBACK_PATH = Path("outputs/feedback/user_feedback_v1.jsonl")
EMPLOYER_SIGNAL_PATH = Path("outputs/feedback/employer_signals_v1.jsonl")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_feedback(payload: dict[str, Any]) -> dict[str, Any]:
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp_utc": _utc_now(),
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
        "run_id": payload.get("run_id"),
        "rating": payload.get("rating"),
        "category": payload.get("category", "general"),
        "message": payload.get("message", ""),
        "meta": payload.get("meta", {}),
    }
    with FEEDBACK_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return {"status": "ok", "path": str(FEEDBACK_PATH), "record": record}


def append_employer_signal(payload: dict[str, Any]) -> dict[str, Any]:
    EMPLOYER_SIGNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp_utc": _utc_now(),
        "company": payload.get("company"),
        "role": payload.get("role"),
        "outcome": payload.get("outcome"),
        "skills_missing": payload.get("skills_missing", []),
        "notes": payload.get("notes", ""),
    }
    with EMPLOYER_SIGNAL_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return {"status": "ok", "path": str(EMPLOYER_SIGNAL_PATH), "record": record}


def list_feedback(limit: int = 100) -> dict[str, Any]:
    if not FEEDBACK_PATH.exists():
        return {"status": "ok", "items": [], "path": str(FEEDBACK_PATH)}
    lines = FEEDBACK_PATH.read_text(encoding="utf-8").splitlines()[-limit:]
    items = [json.loads(x) for x in lines if x.strip()]
    return {"status": "ok", "items": items, "path": str(FEEDBACK_PATH)}
