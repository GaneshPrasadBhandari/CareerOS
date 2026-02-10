#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

if [[ "${1:-}" == "api" ]]; then
  PYTHONPATH=src uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
  exit 0
fi

if [[ "${1:-}" == "ui" ]]; then
  PYTHONPATH=src streamlit run apps/ui/Home.py --server.address 0.0.0.0 --server.port 8501
  exit 0
fi

echo "Usage:"
echo "  scripts/run_phase2_app.sh api   # start FastAPI"
echo "  scripts/run_phase2_app.sh ui    # start Streamlit"
exit 1
