# Phase 3 Bootstrap Guide (Agentic + LLM + API Keys)

This guide starts Phase 3 safely on top of your frozen Phase 2 baseline.

## 1) Prerequisites
- Sync latest `main` (or release branch if you are freezing):
  ```bash
  git checkout main
  git pull origin main
  ```
- Run baseline checks first:
  ```bash
  scripts/run_phase2_tests.sh
  ```

## 2) Create local `.env`
Copy template:
```bash
cp .env.example .env
```

Fill keys you want to use:
- `OPENAI_API_KEY`
- `HUGGINGFACE_API_KEY`
- `TAVILY_API_KEY` (optional)
- `SERPER_API_KEY` (optional)
- optional: `LANGSMITH_API_KEY`, `MCP_SERVER_URL`

> Never commit `.env`.

## 3) Verify readiness from API
Run API:
```bash
scripts/run_phase2_app.sh api
```

Check readiness endpoint:
```bash
curl -s http://127.0.0.1:8000/phase3/readiness | jq
```

## 4) P20 — contract validation
Example request:
```bash
curl -s -X POST http://127.0.0.1:8000/p20/contracts/validate \
  -H 'Content-Type: application/json' \
  -d '{"run_id":"demo_run","agent":"planner","objective":"Plan matching and generation","constraints":{}}' | jq
```

## 5) P21 — dry run orchestration
```bash
curl -s -X POST http://127.0.0.1:8000/p21/langgraph/dry_run \
  -H 'Content-Type: application/json' \
  -d '{"run_id":"demo_run","agent":"planner","objective":"Plan matching and generation","constraints":{}}' | jq
```

Expected: artifact path under `outputs/phase3/`.

## 6) Streamlit checks
Run UI:
```bash
scripts/run_phase2_app.sh ui
```

At bottom of Home page:
- **Check Phase 3 Readiness**
- **Run P20 Contract Validate**
- **Run P21 Dry Run**

## 7) Why this approach
- Keeps P1→P19 stable and demo-safe.
- Adds Phase 3 incrementally with typed contracts.
- Defers live external tool execution until contract + safety gates are validated.
