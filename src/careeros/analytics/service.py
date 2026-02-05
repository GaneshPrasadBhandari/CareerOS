from __future__ import annotations

from typing import Optional, List, Dict
from datetime import datetime

from careeros.analytics.schema import FunnelMetrics, ApplicationSummary, ListApplicationsResponse
from careeros.tracking.service import read_all_jsonl


FUNNEL_STAGES = ["exported", "submitted", "interview", "offer"]


def _parse_dt(s: str) -> Optional[datetime]:
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None


def list_applications(
    tracking_path: str,
    status: Optional[str] = None,
    limit: int = 50,
    newest_first: bool = True,
) -> ListApplicationsResponse:
    rows = read_all_jsonl(tracking_path)

    if status:
        rows = [r for r in rows if r.get("status") == status]

    # sort by created_at_utc
    rows.sort(key=lambda r: _parse_dt(r.get("created_at_utc", "")) or datetime.min, reverse=newest_first)

    items: List[ApplicationSummary] = []
    for r in rows[: max(1, limit)]:
        items.append(ApplicationSummary(
            application_id=r.get("application_id"),
            status=r.get("status"),
            created_at_utc=r.get("created_at_utc"),
            updated_at_utc=r.get("updated_at_utc"),
            package_path=r.get("package_path"),
            validation_report_path=r.get("validation_report_path"),
            export_docx_path=r.get("export_docx_path"),
            export_pdf_path=r.get("export_pdf_path"),
            run_id=r.get("run_id"),
            job_path=r.get("job_path"),
        ))

    return ListApplicationsResponse(total=len(rows), items=items)


def compute_metrics(tracking_path: str) -> FunnelMetrics:
    rows = read_all_jsonl(tracking_path)

    by_status: Dict[str, int] = {}
    for r in rows:
        s = r.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1

    funnel = {k: by_status.get(k, 0) for k in FUNNEL_STAGES}

    def safe_rate(num: int, den: int) -> Optional[float]:
        return round(num / den, 4) if den else None

    conversion = {
        "submitted_over_exported": safe_rate(funnel["submitted"], funnel["exported"]),
        "interview_over_submitted": safe_rate(funnel["interview"], funnel["submitted"]),
        "offer_over_interview": safe_rate(funnel["offer"], funnel["interview"]),
    }

    return FunnelMetrics(
        total=len(rows),
        by_status=by_status,
        funnel=funnel,
        conversion=conversion,
    )


def get_application(tracking_path: str, application_id: str) -> Optional[dict]:
    rows = read_all_jsonl(tracking_path)
    for r in rows:
        if r.get("application_id") == application_id:
            return r
    return None
