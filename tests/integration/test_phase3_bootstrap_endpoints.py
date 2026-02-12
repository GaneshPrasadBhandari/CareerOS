from fastapi.testclient import TestClient

from apps.api.main import app


def test_phase3_readiness_and_contracts():
    c = TestClient(app)

    r = c.get('/phase3/readiness')
    assert r.status_code == 200
    body = r.json()
    assert body['status'] == 'ok'
    assert 'steps' in body

    payload = {
        'run_id': 'test_run',
        'agent': 'planner',
        'objective': 'Plan matching and generation',
        'constraints': {},
    }

    v = c.post('/p20/contracts/validate', json=payload)
    assert v.status_code == 200
    assert v.json()['status'] == 'ok'

    d = c.post('/p21/langgraph/dry_run', json=payload)
    assert d.status_code == 200
    out = d.json()
    assert out['status'] == 'ok'
    assert out['result']['status'] == 'ok'
    assert out['result']['artifact_paths']
