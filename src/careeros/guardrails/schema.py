from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict


class ValidationFinding(BaseModel):
    severity: str                 # "block" | "warn"
    rule_id: str                  # e.g. "GR001"
    message: str
    unsupported_terms: List[str] = Field(default_factory=list)
    evidence_reference: Dict[str, str] = Field(default_factory=dict)  # term -> "missing"


class ValidationReport(BaseModel):
    version: str = "v1"
    run_id: str
    package_path: str
    status: str                   # "pass" | "blocked"
    findings: List[ValidationFinding] = Field(default_factory=list)
