#!/usr/bin/env bash
set -euo pipefail

API_URL="${1:-http://127.0.0.1:8000}"

echo "== Phase3 Doctor =="
echo "Repo: $(pwd)"

printf "\n[1/8] Git status\n"
git status --short --branch || true

printf "\n[2/8] Current branch + commit\n"
git branch --show-current || true
git log --oneline -n 3 || true

printf "\n[3/8] Does P21 route exist in code?\n"
if rg -n '@app.post\("/p21/langgraph/run"\)' apps/api/main.py >/dev/null; then
  echo "OK: /p21/langgraph/run route exists in apps/api/main.py"
else
  echo "ERROR: /p21/langgraph/run route missing in current code checkout"
  echo "Run: git fetch origin --prune && git checkout phase3-dev && git pull --rebase origin phase3-dev"
fi

printf "\n[4/8] Does flow visualization script exist?\n"
if [[ -f scripts/plot_phase3_flow.py ]]; then
  echo "OK: scripts/plot_phase3_flow.py exists"
else
  echo "ERROR: scripts/plot_phase3_flow.py missing in current checkout"
  echo "Run: git fetch origin --prune && git checkout phase3-dev && git pull --rebase origin phase3-dev"
fi

printf "\n[5/8] Test path sanity\n"
if [[ -d tests/unit && -d tests/integration ]]; then
  echo "OK: tests/unit and tests/integration exist"
else
  echo "WARN: expected test folders are missing"
fi

printf "\n[6/8] API readiness check (%s/phase3/readiness)\n" "${API_URL}"
if curl -fsS "${API_URL}/phase3/readiness" >/dev/null 2>&1; then
  echo "OK: API reachable"
  curl -s "${API_URL}/phase3/readiness" | sed -n '1,20p'
else
  echo "WARN: API not reachable at ${API_URL}"
  echo "Start API with: scripts/run_phase2_app.sh api"
fi

printf "\n[7/8] API route smoke checks\n"
if curl -fsS -X POST "${API_URL}/p20/contracts/validate" \
  -H 'Content-Type: application/json' \
  -d '{"run_id":"doctor_run","agent":"planner","objective":"check","constraints":{}}' >/dev/null 2>&1; then
  echo "OK: /p20/contracts/validate available"
else
  echo "WARN: /p20/contracts/validate unavailable"
fi

if curl -fsS -X POST "${API_URL}/p21/langgraph/dry_run" \
  -H 'Content-Type: application/json' \
  -d '{"run_id":"doctor_run","agent":"planner","objective":"check","constraints":{}}' >/dev/null 2>&1; then
  echo "OK: /p21/langgraph/dry_run available"
else
  echo "WARN: /p21/langgraph/dry_run unavailable"
fi

HTTP_CODE=$(curl -s -o /tmp/p21_run_body.json -w "%{http_code}" -X POST "${API_URL}/p21/langgraph/run" \
  -H 'Content-Type: application/json' \
  -d '{"run_id":"doctor_run","top_n":3}' || true)
if [[ "${HTTP_CODE}" == "200" ]]; then
  echo "OK: /p21/langgraph/run available"
else
  echo "WARN: /p21/langgraph/run returned HTTP ${HTTP_CODE}"
  if [[ -f /tmp/p21_run_body.json ]]; then
    echo "Body:"; cat /tmp/p21_run_body.json; echo
  fi
  echo "If body says Not Found, restart API after pulling latest branch."
fi

printf "\n[8/8] Next commands\n"
cat <<'CMDS'
# Sync to latest phase3-dev
git fetch origin --prune
git checkout phase3-dev
git pull --rebase origin phase3-dev

# Re-run tests safely
pytest -q
pytest -q tests/unit tests/integration

# Run visualizer if file exists
python scripts/plot_phase3_flow.py
CMDS
