# CareerOS Local Dev Troubleshooting (macOS + VS Code)

## 1) Path mistakes
If you see:
- `cd/workspace/CareerOS` → this is a typo (missing space).
- `cd /workspace/CareerOS` on macOS → likely invalid path in local machine.

Use these commands instead:

```bash
pwd
git rev-parse --show-toplevel
cd "$(git rev-parse --show-toplevel)"
```

## 2) Branch command mistakes
`which branch` is incorrect for git branch checks.

Use:

```bash
git branch
git branch --show-current
git status
```

## 3) API startup error: `ModuleNotFoundError: No module named 'careeros'`
Run from repo root with `PYTHONPATH=src`:

```bash
PYTHONPATH=src uvicorn apps.api.main:app --reload
```

Or install package in editable mode once:

```bash
pip install -e .
uvicorn apps.api.main:app --reload
```

## 4) Missing dependencies during tests (`docx`, `reportlab`)
Install:

```bash
pip install python-docx reportlab
```

## 5) P18/P19 sections not visible in Streamlit
Likely causes:
1. Running stale branch.
2. API process crashed so UI cannot fetch data.

Check branch and update:

```bash
git branch --show-current
git pull origin main
```

Run UI from repo root:

```bash
PYTHONPATH=src streamlit run apps/ui/Home.py --server.address 0.0.0.0 --server.port 8501
```

## 6) P15 always showing ~95% score
Cause: stale/manual `outputs/state/current_run.json` or inconsistent score scale (0..1 vs 0..100).

Fix now implemented:
- Router auto-derives pending state from latest match artifact when state file is missing.
- Router normalizes score to 0..1 for UI.
- UI metric safely handles both 0..1 and 0..100.

If needed, reset local state file:

```bash
rm -f outputs/state/current_run.json
```

## 7) Quick verification commands

```bash
python -m py_compile apps/api/main.py apps/ui/Home.py apps/api/routes/orchestrator.py
PYTHONPATH=src pytest -q tests/integration/test_api_health.py tests/unit/test_p17_grounded_generation.py tests/unit/test_p14_execute_plan_smoke.py
```

Then run:

```bash
PYTHONPATH=src uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
PYTHONPATH=src streamlit run apps/ui/Home.py --server.address 0.0.0.0 --server.port 8501
```
