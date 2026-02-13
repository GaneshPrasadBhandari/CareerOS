from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.main import app


def test_p25_automation_run_upload_txt_files():
    c = TestClient(app)
    resume_text = Path("data/demo/resume_sample_backend_ml.txt").read_text(encoding="utf-8")
    job_text = Path("data/demo/job_description_ml_platform.txt").read_text(encoding="utf-8")

    files = {
        "resume_file": ("resume.txt", resume_text.encode("utf-8"), "text/plain"),
        "job_file": ("job.txt", job_text.encode("utf-8"), "text/plain"),
    }
    data = {
        "candidate_name": "Upload Demo",
        "top_n": "3",
    }

    r = c.post("/p25/automation/run_upload", files=files, data=data)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["metrics"]["jobs_ingested"] >= 1
    assert Path(body["paths"]["profile_path"]).exists()
