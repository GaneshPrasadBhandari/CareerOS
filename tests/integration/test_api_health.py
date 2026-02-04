# import httpx

# def test_api_health_running():
#     r = httpx.get("http://127.0.0.1:8000/health", timeout=5)
#     assert r.status_code == 200
#     data = r.json()
#     assert data["status"] == "ok"


from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_api_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

