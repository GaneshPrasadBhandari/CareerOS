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


## 8) P21 full deterministic graph run
```bash
curl -s -X POST http://127.0.0.1:8000/p21/langgraph/run \
  -H 'Content-Type: application/json' \
  -d '{"run_id":"demo_run","top_n":3}' | jq
```

This runs load->match->rank->generate->guardrails in one graph call.


## 9) If `tests/integration/test_p21_langgraph_run.py` is missing

If you see:

```bash
ERROR: file or directory not found: tests/integration/test_p21_langgraph_run.py
```

it means your local branch is behind the commit that introduced the P21 end-to-end integration test.

Run this sequence:

```bash
git fetch origin --prune
git checkout phase3-dev
git pull --rebase origin phase3-dev
git ls-files tests/integration
```

Then run either:

```bash
pytest -q
```

or if that specific file exists:

```bash
pytest -q tests/unit tests/integration/test_p21_langgraph_run.py
```

To make the command robust on any branch, use:

```bash
pytest -q tests/unit tests/integration
```

## 10) VS Code quick sync + run checklist

```bash
# Sync
git fetch origin --prune
git checkout phase3-dev
git pull --rebase origin phase3-dev
git status

# Tests
pytest -q

# Run API + UI (separate terminals)
scripts/run_phase2_app.sh api
scripts/run_phase2_app.sh ui

# Optional: visualize current/planned flow
python scripts/plot_phase3_flow.py
```


## 11) If `/p21/langgraph/run` returns `{"detail":"Not Found"}`

This is almost always one of these:
1. local branch is behind (route not present yet), or
2. API server is still running old code and needs restart.

Run exactly:

```bash
git fetch origin --prune
git checkout phase3-dev
git pull --rebase origin phase3-dev
rg -n "@app.post\("/p21/langgraph/run"\)" apps/api/main.py
```

If route exists in file, restart API terminal:

```bash
# stop running API with Ctrl+C, then restart
scripts/run_phase2_app.sh api
```

Then test again:

```bash
curl -s -X POST http://127.0.0.1:8000/p21/langgraph/run \
  -H 'Content-Type: application/json' \
  -d '{"run_id":"demo_run","top_n":3}' | jq
```

## 12) If `python scripts/plot_phase3_flow.py` says file not found

That means your branch does not yet include the script.

```bash
git fetch origin --prune
git checkout phase3-dev
git pull --rebase origin phase3-dev
git ls-files scripts | rg plot_phase3_flow.py
python scripts/plot_phase3_flow.py
```


## 13) One-command diagnostics (recommended)

Run this first when anything is inconsistent:

```bash
scripts/phase3_doctor.sh
```

Optional custom API URL:

```bash
scripts/phase3_doctor.sh http://127.0.0.1:8000
```

It checks:
- current branch + recent commits
- if `/p21/langgraph/run` exists in code
- if `scripts/plot_phase3_flow.py` exists
- API readiness + P20/P21 endpoint availability
- exact next commands to recover

## 14) Common typo in pytest path

If you run this by mistake:

```bash
pytest -q tests/unit_tests/integration
```

you will get `file or directory not found` because folder is wrong.

Use:

```bash
pytest -q tests/unit tests/integration
```
