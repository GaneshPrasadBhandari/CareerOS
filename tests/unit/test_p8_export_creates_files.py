# =========================
# FILE: tests/unit/test_p8_export_creates_files.py
# =========================
import json
from pathlib import Path

from careeros.export.service import export_latest_validated_package


def test_export_creates_docx_and_pdf(tmp_path: Path):
    passed = {
        "version": "v1",
        "run_id": "r2",
        "package_path": "exports/packages/application_package_v1_x.json",
        "status": "pass",
        "findings": [],
    }
    rep_path = tmp_path / "validation_report_v1_pass.json"
    rep_path.write_text(json.dumps(passed), encoding="utf-8")

    pkg = {
        "version": "v1",
        "run_id": "r2",
        "profile_path": "outputs/profile/profile_v1_x.json",
        "job_path": "outputs/jobs/job_post_v1_x.json",
        "bullets": [{"text": "Built pipelines using python and docker"}],
        "evidence_skills": ["python", "docker"],
        "cover_letter": {"subject": "Application", "paragraphs": ["Hello", "Thanks"]},
        "qa_stubs": {"Why fit?": "Overlap in python/docker."},
    }
    pkg_path = tmp_path / "application_package_v1_x.json"
    pkg_path.write_text(json.dumps(pkg), encoding="utf-8")

    meta = export_latest_validated_package(
        package_path=str(pkg_path),
        validation_report_path=str(rep_path),
        out_dir=str(tmp_path / "exports"),
        export_docx=True,
        export_pdf=True,
    )

    assert meta["docx_path"] is not None
    assert meta["pdf_path"] is not None

    assert Path(meta["docx_path"]).exists()
    assert Path(meta["pdf_path"]).exists()
