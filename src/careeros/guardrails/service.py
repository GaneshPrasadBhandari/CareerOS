from __future__ import annotations

import re
import glob
from pathlib import Path
from datetime import datetime

from careeros.parsing.schema import EvidenceProfile
from careeros.generation.schema import ApplicationPackage
from careeros.guardrails.schema import ValidationReport, ValidationFinding


# Simple vocabulary extraction (Phase 0):
# We look for common tech tokens in generated text. Later: NER + structured claim model.
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9\-\+\.]{1,30}")


def extract_tokens(text: str) -> set[str]:
    return set([t.lower() for t in TOKEN_RE.findall(text)])


def validate_package_against_evidence(profile: EvidenceProfile, pkg: ApplicationPackage, run_id: str, package_path: str) -> ValidationReport:
    evidence_skills = set([s.lower() for s in profile.skills])

    # Collect all generated text
    generated_text = []
    for b in pkg.bullets:
        generated_text.append(b.text)
    generated_text.extend(pkg.cover_letter.paragraphs)
    generated_text.extend(list(pkg.qa_stubs.values()))

    text_blob = "\n".join(generated_text).lower()
    tokens = extract_tokens(text_blob)

    # Only check terms that look like skills we care about
    # (use the intersection of tokens with a curated allowlist later)
    # For now: treat any token that appears in pkg evidence_skills as "intended skills",
    # plus any explicit skills that appear in text and are in a small watchlist.
    watchlist = set([
        "python","sql","docker","kubernetes","mlflow","dvc","fastapi","streamlit",
        "rag","langchain","langgraph","pydantic","pytorch","tensorflow","scikit-learn",
        "aws","azure","gcp","llm","genai","vector"
    ])

    mentioned = sorted(list(tokens.intersection(watchlist)))
    unsupported = sorted([t for t in mentioned if t not in evidence_skills])

    findings = []
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


def write_validation_report(report: ValidationReport, out_dir: str = "outputs/guardrails") -> Path:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = Path(out_dir) / f"validation_report_{report.version}_{ts}.json"
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return path


def latest(pattern: str) -> str | None:
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None
