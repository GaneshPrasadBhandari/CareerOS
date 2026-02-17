# =========================
# FILE: tests/unit/test_p8_tracking_append_and_update.py
# =========================
from pathlib import Path

from careeros.tracking.schema import ApplicationRecord
from careeros.tracking.service import append_jsonl, read_all_jsonl, update_status_jsonl, _utc_now


def test_tracking_append_and_update(tmp_path: Path):
    path = tmp_path / "applications_v1.jsonl"

    rec = ApplicationRecord(
        application_id="app_1",
        run_id="r1",
        job_path="j.json",
        package_path="p.json",
        validation_report_path="v.json",
        export_docx_path="d.docx",
        export_pdf_path="d.pdf",
        status="exported",
        created_at_utc=_utc_now(),
        updated_at_utc=_utc_now(),
    )
    append_jsonl(path, rec)

    rows = read_all_jsonl(path)
    assert len(rows) == 1
    assert rows[0]["application_id"] == "app_1"

    updated = update_status_jsonl(path, "app_1", "submitted")
    assert updated is not None
    assert updated.status == "submitted"
