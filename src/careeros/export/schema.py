# =========================
# FILE: src/careeros/export/schema.py
# =========================
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    """
    Phase 0 Export:
    - If package_path/report_path are omitted, API will use "latest" artifacts.
    """
    package_path: Optional[str] = None
    validation_report_path: Optional[str] = None

    export_docx: bool = True
    export_pdf: bool = True

    # Where to write exports
    out_dir: str = "exports/submissions"


class ExportResult(BaseModel):
    version: str = "v1"

    application_id: str
    run_id: str

    package_path: str
    validation_report_path: str

    docx_path: Optional[str] = None
    pdf_path: Optional[str] = None

    status: str = Field(default="exported")
