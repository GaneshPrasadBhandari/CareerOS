# =========================
# FILE: src/careeros/tracking/service.py
# =========================
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from careeros.tracking.schema import ApplicationRecord, ApplicationStatus


def _utc_now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_parent(path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def append_jsonl(path: str | Path, record: ApplicationRecord) -> Path:
    p = ensure_parent(path)
    with p.open("a", encoding="utf-8") as f:
        f.write(record.model_dump_json())
        f.write("\n")
    return p


def read_all_jsonl(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    rows = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def update_status_jsonl(
    path: str | Path,
    application_id: str,
    new_status: ApplicationStatus,
) -> Optional[ApplicationRecord]:
    """
    Phase 0 approach: rewrite file (ok for capstone scale).
    """
    p = Path(path)
    if not p.exists():
        return None

    rows = read_all_jsonl(p)
    updated = None
    now = _utc_now()

    for r in rows:
        if r.get("application_id") == application_id:
            r["status"] = new_status
            r["updated_at_utc"] = now
            updated = r

    if updated is None:
        return None

    ensure_parent(p)
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False))
            f.write("\n")

    return ApplicationRecord.model_validate(updated)
