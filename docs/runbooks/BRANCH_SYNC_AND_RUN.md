# Branch Sync + Run Commands (GitHub -> Local)

If UI still shows old text like `Step 3: Grounded Evidence Analysis` + comma-separated error,
it means local code is behind the branch that contains latest P15/P17 fixes.

## 1) Check current branch and commit
```bash
git branch --show-current
git log --oneline -n 5
```

## 2) Pull correct branch
If fixes were merged to `main`:
```bash
git checkout main
git pull origin main
```

If fixes are in a feature branch:
```bash
git fetch origin
git checkout <branch_name>
git pull origin <branch_name>
```

## 3) Confirm fixed UI text exists in local file
```bash
rg -n "P17 — Grounded Evidence Analysis|Refresh from Latest Match|orchestrator/reset" apps/ui/Home.py apps/api/routes/orchestrator.py
```

Expected matches:
- `P17 — Grounded Evidence Analysis` in `apps/ui/Home.py`
- `Refresh from Latest Match` in `apps/ui/Home.py`
- `/orchestrator/reset` in `apps/api/routes/orchestrator.py`

## 4) Run tests and app
```bash
scripts/run_phase2_tests.sh
```

Terminal 1:
```bash
scripts/run_phase2_app.sh api
```

Terminal 2:
```bash
scripts/run_phase2_app.sh ui
```

## 5) What reject does in P15
- `Reject & Re-Run Match/Rank` will automatically call P4 + P5 again on latest artifacts.
- If you want new behavior, update P2/P3 text first and rerun those steps.
