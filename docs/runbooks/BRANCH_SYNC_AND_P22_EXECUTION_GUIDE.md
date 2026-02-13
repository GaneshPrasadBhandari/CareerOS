# Branch Sync + P22 Execution Guide (Simple, No-Confusion Flow)

This guide is the **single source of truth** for day-to-day Git and P22 execution.

---

## 1) First confusion fix: how to exit the `(END)` screen

When `git branch -vv` opens in a pager (`less`) and shows `(END)`:
- press `q` to quit the pager.

If your shell keeps using pager too often, disable pager for that command:

```bash
git --no-pager branch -vv
```

Or disable globally:

```bash
git config --global pager.branch false
```

---

## 2) Minimal branch model to keep

Keep only:
- `main`
- `release/phase1-v1.0`
- `release/phase2-v1.0`
- `phase3-dev`

Everything else can be deleted once merged/backed up.

---

## 3) Commands to delete extra local branches safely

> Run from local machine in VS Code terminal.

```bash
# fetch latest refs first
git fetch origin --prune

# check merged branches into phase3-dev
# (delete only what is already merged)
git checkout phase3-dev
git branch --merged

# delete example extra branches (adjust if still needed)
git branch -d backup/local-wip-20260210-1214
git branch -d feat/p17-followup
git branch -d feat/p21-langgraph-node1
git branch -d hotfix/restore-phase1
git branch -d phase2-dev

# if Git says not fully merged but you truly want to remove:
# git branch -D <branch>
```

Delete remote branches (optional, only if merged and not needed):

```bash
git push origin --delete feat/p17-followup
git push origin --delete feat/p21-langgraph-node1
git push origin --delete hotfix/restore-phase1
git push origin --delete phase2-dev
```

---

## 4) Standard workflow with Codex + VS Code

### Rule
- Integration branch for active Phase 3 work = `phase3-dev`.
- Every task gets its own feature branch from `phase3-dev`.

### For P22 (recommended naming)

```bash
git checkout phase3-dev
git pull origin phase3-dev
git checkout -b feat/p22-approval-nodes
```

Do your work, run tests, commit, push, open PR to `phase3-dev`:

```bash
pytest -q
git add .
git commit -m "P22: add approval nodes and API gate controls"
git push -u origin feat/p22-approval-nodes
```

After PR merge to `phase3-dev`, periodically promote to `main`:

```bash
git checkout main
git pull origin main
git merge origin/phase3-dev
git push origin main
```

---

## 5) Keeping VS Code always up-to-date

Daily start:

```bash
git fetch origin --prune
git checkout phase3-dev
git pull --rebase origin phase3-dev
```

Before starting a new feature branch:

```bash
git checkout phase3-dev
git pull --rebase origin phase3-dev
git checkout -b feat/<task-name>
```

---

## 6) Generated/untracked files cleanup

If you want to keep a temporary snapshot:

```bash
git stash push -u -m "temp-runtime-artifacts"
```

If you want to remove untracked generated files:

```bash
git clean -nd   # preview
git clean -fd   # delete
```

---

## 7) P22 implementation plan (what, why, models, automation)

### Objective
Implement **human approval nodes** in the LangGraph orchestration so sensitive actions remain explicitly human-controlled.

### Why
P22 is the trust/governance bridge between autonomous generation and safe execution.

### Scope
1. Add approval state model (`pending_approval`, `approved`, `rejected`).
2. Insert approval node after guardrails in LangGraph flow.
3. Add API endpoint(s):
   - submit approval decision
   - query approval status
4. Persist approval decisions as run artifacts for audit.
5. Add integration tests for approve/reject paths.

### LLM/model strategy
- **Default deterministic path** for matching/ranking/guardrails.
- **LLM usage** only where text synthesis is needed (generation).
- Model routing recommendation:
  - low-cost open model for routine drafting
  - stronger hosted model only for complex rewrite or edge-case reasoning
- Keep all approval decisions human-provided, never auto-approved by model.

### Automation split
- Automated: load context, match, rank, generate draft, guardrails validate.
- Human-in-the-loop: final approval for shortlist/package/sensitive send action.

---

## 8) P22 acceptance checklist

- [ ] `phase3-dev` synced and clean
- [ ] `feat/p22-approval-nodes` branch created
- [ ] approval node added to graph
- [ ] API endpoints for approval decision + status
- [ ] artifacts written under outputs for audit trail
- [ ] tests pass (`pytest -q`)
- [ ] PR merged into `phase3-dev`
- [ ] optional promotion merge `phase3-dev` -> `main`
