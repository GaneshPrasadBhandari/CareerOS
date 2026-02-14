#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient

from apps.api.main import app


def test_p25_trace_latest_endpoint_after_run():
    c = TestClient(app)

    # create a run first
    run_resp = c.post(
        "/p25/automation/run",
        json={
            "run_id": "itest_trace",
            "candidate_name": "Trace User",
            "resume": {"source_type": "inline", "text": "Python FastAPI SQL Docker LangGraph"},
            "jobs": {"job_texts": ["Looking for Python FastAPI SQL Docker engineer"]},
        },
    )
    assert run_resp.status_code == 200
    assert run_resp.json().get("status") == "ok"

    latest = c.get("/p25/automation/trace/latest", params={"run_id": "itest_trace"})
    assert latest.status_code == 200
    body = latest.json()
    assert body["status"] == "ok"
    assert "trace" in body
    assert "layers" in body["trace"]
    assert "L2_parsing" in body["trace"]["layers"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__]))
