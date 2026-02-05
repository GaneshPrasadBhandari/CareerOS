from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel


class FunnelMetrics(BaseModel):
    version: str = "v1"
    total: int
    by_status: Dict[str, int]
    funnel: Dict[str, int]
    conversion: Dict[str, Optional[float]]


class ApplicationSummary(BaseModel):
    application_id: str
    status: str
    created_at_utc: str
    updated_at_utc: str

    package_path: str
    validation_report_path: str

    export_docx_path: Optional[str] = None
    export_pdf_path: Optional[str] = None

    run_id: Optional[str] = None
    job_path: Optional[str] = None


class ListApplicationsResponse(BaseModel):
    version: str = "v1"
    total: int
    items: List[ApplicationSummary]
