import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.main import app


def test_p25_automation_run_upload_auto_txt_resume(monkeypatch):
    c = TestClient(app)

    if importlib.util.find_spec("multipart") is None:
        r = c.post("/p25/automation/run_upload_auto")
        assert r.status_code == 200
        assert r.json()["status"] == "error"
        return

    # avoid outbound calls in test
    from careeros.phase3 import next_steps

    monkeypatch.setattr(
        next_steps,
        "discover_job_urls_for_roles",
        lambda **kwargs: {
            "status": "ok",
            "urls": [],
            "job_texts": ["Senior ML Engineer role requiring Python, FastAPI, SQL, Docker"],
            "urls_by_role": {"ML Engineer": []},
            "errors": [],
            "daily_limit": 20,
            "sources": ["mock"],
        },
    )

    resume_text = Path("data/demo/resume_sample_backend_ml.txt").read_text(encoding="utf-8")
    files = {
        "resume_file": ("resume.txt", resume_text.encode("utf-8"), "text/plain"),
    }
    data = {
        "candidate_name": "Upload Auto Demo",
        "top_n": "3",
        "roles_csv": "ML Engineer,Backend Engineer",
        "location": "USA",
        "daily_limit": "20",
        "private_mode": "true",
    }

    r = c.post("/p25/automation/run_upload_auto", files=files, data=data)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["metrics"]["jobs_ingested"] >= 1
    assert "hitl" in body
