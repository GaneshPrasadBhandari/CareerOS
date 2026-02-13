from fastapi.testclient import TestClient

from apps.api.main import app


def test_p24_v2_and_p25_health_endpoints():
    c = TestClient(app)

    r = c.post(
        "/p24/evaluator/run_v2",
        json={
            "run_id": "itest_v2",
            "weights": {
                "match_quality": 30,
                "guardrails_quality": 25,
                "approval_quality": 20,
                "package_quality": 15,
                "pipeline_reliability": 10,
            },
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "summary" in body
    assert "overall_score" in body["summary"]

    latest = c.get("/p24/evaluator/latest", params={"run_id": "itest_v2"})
    assert latest.status_code == 200
    assert latest.json().get("status") in {"ok", "idle"}

    health = c.get("/p25/system/health")
    assert health.status_code == 200
    h = health.json()
    assert "status" in h
    assert "checks" in h
    assert "llm" in h["checks"]
    assert "vector_db" in h["checks"]
