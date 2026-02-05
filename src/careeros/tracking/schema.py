# =========================
# FILE: src/careeros/tracking/schema.py
# =========================
from __future__ import annotations

from typing import Optional, Literal
from pydantic import BaseModel, Field


ApplicationStatus = Literal[
    "draft",
    "validated",
    "exported",
    "submitted",
    "rejected",
    "interview",
    "offer",
    "withdrawn",
]


class ApplicationRecord(BaseModel):
    version: str = "v1"

    application_id: str
    run_id: str

    job_path: Optional[str] = None
    package_path: str
    validation_report_path: str

    export_docx_path: Optional[str] = None
    export_pdf_path: Optional[str] = None

    status: ApplicationStatus = Field(default="exported")

    created_at_utc: str
    updated_at_utc: str
