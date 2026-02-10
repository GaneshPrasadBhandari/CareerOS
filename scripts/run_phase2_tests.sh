#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "[1/4] Python syntax check"
python -m py_compile apps/api/main.py apps/ui/Home.py apps/api/routes/orchestrator.py src/api/routes/orchestrator.py

echo "[2/4] Ensure local deps"
pip install -q python-docx reportlab

echo "[3/4] Run targeted tests"
PYTHONPATH=src pytest -q \
  tests/integration/test_api_health.py \
  tests/unit/test_p17_grounded_generation.py \
  tests/unit/test_p14_execute_plan_smoke.py

echo "[4/4] Quick API endpoint sanity"
PYTHONPATH=src python - <<'PY'
from fastapi.testclient import TestClient
from apps.api.main import app
c = TestClient(app)
print('health', c.get('/health').status_code)
print('phases', c.get('/phases/status').status_code)
print('p15_current', c.get('/orchestrator/current_state').status_code)
print('p15_refresh', c.get('/orchestrator/current_state', params={'refresh': True}).status_code)
print('p15_reset', c.post('/orchestrator/reset').status_code)
PY

echo "✅ Phase2 tests complete"
