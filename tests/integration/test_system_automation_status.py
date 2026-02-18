from fastapi.testclient import TestClient

from apps.api.main import app


def test_system_automation_status_contract():
    client = TestClient(app)
    resp = client.get('/system/automation/status')
    assert resp.status_code == 200
    body = resp.json()
    assert body['status'] == 'ok'
    assert body['automation_layers']['L9_vector_indexing'] is True
    assert 'integrations' in body
