from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.main import app


def test_storage_status_endpoint_shape():
    c = TestClient(app)
    r = c.get('/system/storage/status')
    assert r.status_code == 200
    body = r.json()
    assert body['status'] == 'ok'
    assert 'storage' in body
    assert 'vector_db' in body


def test_p25_response_contains_hitl():
    c = TestClient(app)

    resume_text = Path('data/demo/resume_sample_backend_ml.txt').read_text(encoding='utf-8')
    job_text = Path('data/demo/job_description_ml_platform.txt').read_text(encoding='utf-8')

    r = c.post(
        '/p25/automation/run',
        json={
            'run_id': 'itest_hitl',
            'candidate_name': 'Demo',
            'privacy': {'private_mode': True},
            'resume': {'source_type': 'inline', 'text': resume_text},
            'jobs': {'job_texts': [job_text]},
        },
    )

    assert r.status_code == 200
    body = r.json()
    assert body['status'] == 'ok'
    assert 'hitl' in body
    assert 'confidence_percent' in body['hitl']
    assert 'approval_required' in body['hitl']
