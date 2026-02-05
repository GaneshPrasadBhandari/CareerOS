# =========================
# FILE: tests/unit/test_p8_export_gates_on_guardrails.py
# =========================
import json
from pathlib import Path

import pytest

from careeros.export.service import export_latest_validated_package
from careeros.guardrails.schema import ValidationReport


def test_export_blocks_when_validation_is_blocked(tmp_path: Path, monkeypatch):
    # Create fake blocked validation report file
    blocked = {
        "version": "v1",
        "run_id": "r1",
        "package_path": "exports/packages/application_package_v1_x.json",
        "status": "blocked",
        "findings": [{"severity": "block", "rule_id": "GR001", "message": "x", "unsupported_terms": ["snowflake"], "evidence_reference": {"snowflake": "missing"}}],
    }
    rep_path = tmp_path / "validation_report_v1_1.json"
    rep_path.write_text(json.dumps(blocked), encoding="utf-8")

    # Create a minimal valid ApplicationPackage file (use your real schema)
    pkg = {
        "version": "v1",
        "run_id": "r1",
        "profile_path": "outputs/profile/profile_v1_x.json",
        "job_path": "outputs/jobs/job_post_v1_x.json",
        "bullets": [{"text": "Using python and docker"}],
        "evidence_skills": ["python", "docker"],
        "cover_letter": {"subject": "s", "paragraphs": ["p1"]},
        "qa_stubs": {"Why fit?": "Because..."},
    }
    pkg_path = tmp_path / "application_package_v1_x.json"
    pkg_path.write_text(json.dumps(pkg), encoding="utf-8")

    with pytest.raises(ValueError):
        export_latest_validated_package(
            package_path=str(pkg_path),
            validation_report_path=str(rep_path),
            out_dir=str(tmp_path / "out"),
            export_docx=True,
            export_pdf=True,
        )
