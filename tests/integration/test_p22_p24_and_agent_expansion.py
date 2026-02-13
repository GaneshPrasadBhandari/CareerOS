from fastapi.testclient import TestClient

from apps.api.main import app


def test_p22_p23_p24_and_expansion_endpoints():
    c = TestClient(app)

    # P22 approval decision + readback
    d = c.post(
        "/p22/approval/decision",
        json={"run_id": "itest_phase3", "approved": True, "reviewer": "qa", "notes": "looks good"},
    )
    assert d.status_code == 200
    assert d.json()["status"] == "ok"

    latest = c.get("/p22/approval/latest", params={"run_id": "itest_phase3"})
    assert latest.status_code == 200
    assert latest.json().get("status") in {"ok", "idle"}

    # P23 memory upsert + get
    up = c.post(
        "/p23/memory/upsert",
        json={"run_id": "itest_phase3", "namespace": "profile", "key": "target_role", "value": "ML Engineer"},
    )
    assert up.status_code == 200
    assert up.json()["status"] == "ok"

    getm = c.get(
        "/p23/memory/get",
        params={"run_id": "itest_phase3", "namespace": "profile", "key": "target_role"},
    )
    assert getm.status_code == 200
    assert getm.json()["status"] == "ok"
    assert getm.json()["value"] == "ML Engineer"

    # P24 evaluator run
    ev = c.post("/p24/evaluator/run", json={"run_id": "itest_phase3"})
    assert ev.status_code == 200
    assert ev.json()["status"] == "ok"
    assert "summary" in ev.json()

    # Expansion agents stubs
    parser = c.post("/agents/parser/extract", json={"source_type": "inline", "text": "Python FastAPI"})
    assert parser.status_code == 200
    assert parser.json()["status"] == "ok"

    vision = c.post("/agents/vision/ocr", json={"mock_ocr_text": "Detected resume text"})
    assert vision.status_code == 200
    assert vision.json()["status"] == "ok"

    conn = c.post("/agents/connector/ingest", json={"source": "csv_import", "items_ingested": 2})
    assert conn.status_code == 200
    assert conn.json()["status"] == "ok"
