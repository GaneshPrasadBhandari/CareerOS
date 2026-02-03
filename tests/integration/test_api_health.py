import httpx

def test_api_health_running():
    r = httpx.get("http://127.0.0.1:8000/health", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
