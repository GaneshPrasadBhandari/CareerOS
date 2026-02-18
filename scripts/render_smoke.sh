#!/usr/bin/env bash
set -euo pipefail

API_URL="${1:-https://careeros-backend-d9sc.onrender.com}"
UI_URL="${2:-https://career-os-final-test.streamlit.app}"

echo "== CareerOS Render smoke =="
echo "API: $API_URL"
echo "UI : $UI_URL"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing command: $1"; exit 1; }; }
need curl
need python

json_pp() {
  python - <<'PY'
import json,sys
raw=sys.stdin.read().strip()
try:
  print(json.dumps(json.loads(raw), indent=2)[:4000])
except Exception:
  print(raw[:4000])
PY
}

check_get() {
  local name="$1"; shift
  local url="$1"
  echo "\n-- $name"
  resp="$(curl -sS -m 40 "$url")"
  echo "$resp" | json_pp
}

check_get "API /health" "$API_URL/health"
check_get "API /phases/status" "$API_URL/phases/status"
check_get "API /p25/system/health" "$API_URL/p25/system/health"
check_get "API /feedback/list?limit=5" "$API_URL/feedback/list?limit=5"

echo "\n-- API /p25/automation/run (minimal inline payload)"
resume="$(python - <<'PY'
from pathlib import Path
print(Path('data/demo/resume_sample_backend_ml.txt').read_text(encoding='utf-8'))
PY
)"
job="$(python - <<'PY'
from pathlib import Path
print(Path('data/demo/job_description_ml_platform.txt').read_text(encoding='utf-8'))
PY
)"

payload="$(python - <<PY
import json
print(json.dumps({
  'run_id': 'render_smoke_run',
  'candidate_name': 'Render Smoke',
  'privacy': {'private_mode': True},
  'top_n': 3,
  'resume': {'source_type': 'inline', 'text': '''$resume'''},
  'jobs': {'job_texts': ['''$job''']}
}))
PY
)"

p25_resp="$(curl -sS -m 90 -X POST "$API_URL/p25/automation/run" -H 'Content-Type: application/json' -d "$payload")"
echo "$p25_resp" | json_pp

echo "\n-- API /p25/automation/trace/latest?run_id=render_smoke_run"
check_get "API trace" "$API_URL/p25/automation/trace/latest?run_id=render_smoke_run"

echo "\n-- API /feedback/submit"
fb_payload='{"run_id":"render_smoke_run","rating":5,"comment":"render smoke ok","source":"smoke_script"}'
fb_resp="$(curl -sS -m 40 -X POST "$API_URL/feedback/submit" -H 'Content-Type: application/json' -d "$fb_payload")"
echo "$fb_resp" | json_pp

echo "\n-- UI HEAD/GET"
curl -sSI -m 40 "$UI_URL" | sed -n '1,20p'

echo "\nRender smoke completed."
