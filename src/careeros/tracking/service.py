# =========================
# FILE: src/careeros/tracking/service.py
# =========================
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

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




def create_application_record(
    *,
    run_id: str,
    job_path: Optional[str],
    package_path: str,
    validation_report_path: str,
    export_docx_path: Optional[str] = None,
    export_pdf_path: Optional[str] = None,
    status: ApplicationStatus = "exported",
) -> ApplicationRecord:
    """
    Stable constructor used by P8/P12.
    Creates a new ApplicationRecord with a unique application_id.
    """
    app_id = f"app_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    now = _utc_now()

    return ApplicationRecord(
        version="v1",
        application_id=app_id,
        run_id=run_id,
        job_path=job_path,
        package_path=package_path,
        validation_report_path=validation_report_path,
        export_docx_path=export_docx_path,
        export_pdf_path=export_pdf_path,
        status=status,
        created_at_utc=now,
        updated_at_utc=now,
    )


def write_application_record(
    record: ApplicationRecord,
    *,
    tracking_path: str = "outputs/apply_tracking/applications_v1.jsonl",
) -> str:
    """
    Stable writer used by P8/P12.
    Appends one record to the JSONL ledger.
    """
    p = append_jsonl(tracking_path, record)
    return str(p)
