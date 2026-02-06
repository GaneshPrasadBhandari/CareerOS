from fastapi.testclient import TestClient
from apps.api.mainold import app

client = TestClient(app)

def test_api_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

