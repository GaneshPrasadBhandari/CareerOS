from fastapi.testclient import TestClient

from apps.api.main import app


def test_p21_langgraph_run_end_to_end_minimal():
    c = TestClient(app)

    profile_resp = c.post(
        "/profile",
        json={"candidate_name": "Demo", "resume_text": "Python FastAPI SQL Docker AWS pytest"},
    )
    assert profile_resp.status_code == 200
    profile_path = profile_resp.json()["path"]

    job_resp = c.post(
        "/jobs/ingest",
        json={"job_text": "Need Python FastAPI SQL and Docker on AWS", "url": None},
    )
    assert job_resp.status_code == 200
    job_path = job_resp.json()["path"]

    run_resp = c.post(
        "/p21/langgraph/run",
        json={"run_id": "itest_p21", "profile_path": profile_path, "job_path": job_path, "top_n": 3},
    )
    assert run_resp.status_code == 200
    body = run_resp.json()
    assert body["status"] == "ok"
    result = body["result"]
    assert result.get("match_path")
    assert result.get("shortlist_path")
    assert result.get("package_path")
    assert result.get("validation_report_path")
    assert result.get("validation_status") in {"pass", "blocked"}
