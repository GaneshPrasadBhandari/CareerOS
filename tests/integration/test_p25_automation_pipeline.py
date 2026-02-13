from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.main import app


def test_p25_automation_pipeline_with_demo_texts():
    client = TestClient(app)

    resume_text = Path("data/demo/resume_sample_backend_ml.txt").read_text(encoding="utf-8")
    job_text = Path("data/demo/job_description_ml_platform.txt").read_text(encoding="utf-8")

    resp = client.post(
        "/p25/automation/run",
        json={
            "run_id": "itest_p25_auto",
            "candidate_name": "Riya Patel",
            "top_n": 3,
            "resume": {"source_type": "inline", "text": resume_text},
            "jobs": {"job_texts": [job_text]},
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["run_id"] == "itest_p25_auto"
    assert body["metrics"]["jobs_ingested"] >= 1
    assert body["metrics"]["ranked_items"] >= 1
    assert body["metrics"]["guardrails_status"] in {"pass", "blocked"}

    paths = body["paths"]
    assert Path(paths["profile_path"]).exists()
    assert Path(paths["first_job_path"]).exists()
    assert Path(paths["match_path"]).exists()
    assert Path(paths["shortlist_path"]).exists()
    assert Path(paths["package_path"]).exists()
    assert Path(paths["validation_report_path"]).exists()


    package_json = Path(paths["package_path"]).read_text(encoding="utf-8")
    assert package_json
    import json as _json
    pkg = _json.loads(package_json)
    assert len(pkg.get("bullets", [])) >= 5
    assert len(pkg.get("cover_letter", {}).get("paragraphs", [])) >= 4

    assert body["llm_summary"]["status"] in {"ok", "degraded"}
