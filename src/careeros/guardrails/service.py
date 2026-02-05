from __future__ import annotations

import glob
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from careeros.parsing.schema import EvidenceProfile
from careeros.generation.schema import ApplicationPackage
from careeros.guardrails.schema import ValidationReport, ValidationFinding


# Token pattern: words + common tool spellings (fastapi, scikit-learn, gpt4, yolo8, etc.)
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9\-\+\.]{1,40}")


def latest(pattern: str) -> Optional[str]:
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_validation_report(report: ValidationReport, out_dir: str = "outputs/guardrails") -> Path:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = Path(out_dir) / f"validation_report_{report.version}_{ts}.json"
    out_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return out_path


def validate_package_against_evidence(
    profile: EvidenceProfile,
    pkg: ApplicationPackage,
    run_id: str,
    package_path: str,
) -> ValidationReport:
    """
    P7 Guardrails (Phase 0 — STRICTLY LOW FALSE POSITIVE)

    Rule:
      Only block when we see a KNOWN tech/tool term in generated output
      that is not present in EvidenceProfile.skills.

    We intentionally DO NOT attempt "skill inference" from general prose.
    This prevents false blocks like: thank/team/hiring/apis/etc.
    """

    evidence_skills = {s.lower().strip() for s in (profile.skills or []) if s and s.strip()}

    # High-signal tool watchlist only (NO generic nouns)
    watchlist = {
        # core dev
        "python", "sql", "docker", "kubernetes", "fastapi", "streamlit", "pydantic",
        "pytest", "git", "linux",

        # data / ops tools
        "mlflow", "dvc", "airflow", "terraform", "kafka",
        "spark", "databricks", "snowflake",

        # clouds / services
        "aws", "azure", "gcp", "sagemaker", "ecr", "eks",

        # llm/rag stack (optional but ok)
        "llm", "genai", "rag", "langchain", "langgraph",
        "faiss", "chroma",
        "pytorch", "tensorflow", "scikit-learn",
    }

    # Collect generated text segments
    segments: List[str] = []

    bullets = getattr(pkg, "bullets", []) or []
    for b in bullets:
        segments.append(getattr(b, "text", "") or "")

    cover = getattr(pkg, "cover_letter", None)
    if cover and getattr(cover, "paragraphs", None):
        segments.extend([p or "" for p in cover.paragraphs])

    qa = getattr(pkg, "qa_stubs", None) or {}
    if isinstance(qa, dict):
        segments.extend([(v or "") for v in qa.values()])

    # Detect unsupported tool mentions
    unsupported_set: set[str] = set()

    for seg in segments:
        if not seg:
            continue
        for tok in TOKEN_RE.findall(seg):
            t = tok.lower().strip()
            # only enforce for known tools
            if t in watchlist and t not in evidence_skills:
                unsupported_set.add(t)

    unsupported = sorted(unsupported_set)

    findings: list[ValidationFinding] = []
    status = "pass"

    if unsupported:
        status = "blocked"
        findings.append(
            ValidationFinding(
                severity="block",
                rule_id="GR001",
                message="Unsupported skills detected in generated package. Remove or replace with evidence-backed skills.",
                unsupported_terms=unsupported,
                evidence_reference={t: "missing" for t in unsupported},
            )
        )

    return ValidationReport(
        run_id=run_id,
        package_path=package_path,
        status=status,
        findings=findings,
    )
