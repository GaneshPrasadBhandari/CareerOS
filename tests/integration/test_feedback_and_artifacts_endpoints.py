from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.main import app


def test_feedback_submit_and_list():
    c = TestClient(app)
    r = c.post(
        "/feedback/submit",
        json={
            "user_id": "u1",
            "email": "u1@example.com",
            "run_id": "r1",
            "rating": 5,
            "category": "general",
            "message": "Great output",
        },
    )
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    lr = c.get("/feedback/list", params={"limit": 5})
    assert lr.status_code == 200
    assert lr.json()["status"] == "ok"
    assert isinstance(lr.json()["items"], list)


def test_artifacts_read_and_open_json_file():
    c = TestClient(app)
    fp = Path("outputs") / "test_artifact_read.json"
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text('{"hello": "world"}', encoding="utf-8")

    rr = c.get("/artifacts/read", params={"path": str(fp)})
    assert rr.status_code == 200
    body = rr.json()
    assert body["status"] == "ok"
    assert "hello" in body["content"]

    ro = c.get("/artifacts/open", params={"path": str(fp)})
    assert ro.status_code == 200


def test_artifacts_path_restricted():
    c = TestClient(app)
    rr = c.get("/artifacts/read", params={"path": "/etc/passwd"})
    assert rr.status_code == 400
