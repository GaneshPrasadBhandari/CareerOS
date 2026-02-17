import json
from pathlib import Path
import pytest

from careeros.export.service import export_latest_validated_package


def test_export_blocks_when_validation_blocked(tmp_path: Path):
    rep_path = tmp_path / "validation_report.json"
    rep_path.write_text(json.dumps({
        "version": "v1",
        "run_id": "r1",
        "package_path": "pkg.json",
        "status": "blocked",
        "findings": [{"severity": "block", "rule_id": "GR001", "message": "x", "unsupported_terms": ["snowflake"], "evidence_reference": {"snowflake": "missing"}}],
    }), encoding="utf-8")

    pkg_path = tmp_path / "package.json"
    pkg_path.write_text(json.dumps({
        "version": "v1",
        "run_id": "r1",
        "profile_path": "p.json",
        "job_path": "j.json",
        "bullets": [{"text": "python docker"}],
        "evidence_skills": ["python", "docker"],
        "cover_letter": {"subject": "s", "paragraphs": ["p"]},
        "qa_stubs": {"Why?": "x"},
    }), encoding="utf-8")

    with pytest.raises(ValueError):
        export_latest_validated_package(
            package_path=str(pkg_path),
            validation_report_path=str(rep_path),
            out_dir=str(tmp_path / "out"),
            export_docx=True,
            export_pdf=True,
        )


def test_export_creates_docx_and_pdf(tmp_path: Path):
    rep_path = tmp_path / "validation_report.json"
    rep_path.write_text(json.dumps({
        "version": "v1",
        "run_id": "r2",
        "package_path": "pkg.json",
        "status": "pass",
        "findings": [],
    }), encoding="utf-8")

    pkg_path = tmp_path / "package.json"
    pkg_path.write_text(json.dumps({
        "version": "v1",
        "run_id": "r2",
        "profile_path": "p.json",
        "job_path": "outputs/jobs/job_post_v1_test.json",
        "bullets": [{"text": "Built APIs using python and docker"}],
        "evidence_skills": ["python", "docker"],
        "cover_letter": {"subject": "Application", "paragraphs": ["Hello", "Thanks"]},
        "qa_stubs": {"Why fit?": "Overlap python/docker"},
    }), encoding="utf-8")

    meta = export_latest_validated_package(
        package_path=str(pkg_path),
        validation_report_path=str(rep_path),
        out_dir=str(tmp_path / "exports"),
        export_docx=True,
        export_pdf=True,
    )

    assert meta["docx_path"] and Path(meta["docx_path"]).exists()
    assert meta["pdf_path"] and Path(meta["pdf_path"]).exists()
