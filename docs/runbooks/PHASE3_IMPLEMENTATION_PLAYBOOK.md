# Phase 3 Implementation Playbook (Professional Workflow)

This playbook explains **what to do, why, and in which order** for P20+.

---

## A) Branch strategy (professional flow)

Use this model:
1. `main` = stable integration branch
2. `release/phase2-v1.0` = frozen demo baseline
3. `phase3-dev` = long-lived integration branch for Phase 3
4. Feature branches from `phase3-dev`:
   - `feat/p20-contracts`
   - `feat/p21-langgraph-dryrun`
   - `feat/p22-approval-nodes`

### Commands
```bash
git checkout main
git pull origin main
git checkout -b phase3-dev
git push -u origin phase3-dev
```

For each step:
```bash
git checkout phase3-dev
git pull origin phase3-dev
git checkout -b feat/p20-contracts
# work + tests
git push -u origin feat/p20-contracts
```

---

## B) API keys and where to get them (free/entry tiers)

### Required now (for readiness visibility)
- `OPENAI_API_KEY`
- `HUGGINGFACE_API_KEY`

### Optional (web/search/routing)
- `TAVILY_API_KEY`
- `SERPER_API_KEY`

### Optional observability/tooling
- `LANGSMITH_API_KEY`
- `MCP_SERVER_URL`

### Setup
```bash
cp .env.example .env
```
Fill values in `.env`.

---

## C) What each key does in this architecture

- `OPENAI_API_KEY`: paid/hosted LLM inference (generation/planning).
- `HUGGINGFACE_API_KEY`: open model inference endpoints or model downloads.
- `TAVILY_API_KEY`: search/retrieval augmentation (optional).
- `SERPER_API_KEY`: Google-style search API (optional).
- `LANGSMITH_API_KEY`: traces and observability for chain/graph executions.
- `MCP_SERVER_URL`: future MCP tool endpoint for standardized tool calling.

---

## D) L-layer mapping for P20+ (from architecture)

- **L2 API**: endpoints `/p20/contracts/validate`, `/p21/langgraph/dry_run`.
- **L3 Orchestration**: LangGraph flow introduced in P21.
- **L4 Agent layer**: typed agent tasks (`planner`, `matcher`, `generator`, etc.).
- **L5 Approval**: explicit human approval nodes (P22).
- **L6 Execution/Tracking**: artifact outputs in `outputs/phase3/` + existing ledgers.
- **L8 Memory/Models**: providers + vector/DB integrations stepwise.
- **L9 Governance**: contract validation + guardrails + logs.

---

## E) Manual vs automated (what changed)

### Before (manual)
You clicked each phase button individually (P1->P19).

### Now (automation bootstrap)
- P20 validates contracts automatically.
- P21 dry-run executes standardized step and writes artifacts.
- Next, P21 full graph will chain steps automatically.

So automation starts with **contract + dry-run**, then expands to full graph orchestration.

---

## F) Folder organization standard (recommended)

Keep these cleanly separated:
- `data/` raw input files (resume/JD source)
- `outputs/` operational artifacts (`profile`, `jobs`, `matching`, `ranking`, `phase3`, etc.)
- `exports/` user-facing deliverables (resume package, cover letter files)
- `logs/` runtime logs (`careeros.jsonl`)
- `docs/runbooks/` operational guides
- `src/careeros/` core business logic
- `apps/` API and UI entrypoints

---

## G) Country/format handling (USA ATS default)

Current default generation behavior is generic and safe. For production clarity:
1. Add `country_code` (default `US`) into intake constraints.
2. Add template selector in generation service:
   - `US_ATS`
   - `EUROPASS`
   - `UK_STANDARD`
3. Route bullet and cover letter wording by template.
4. Keep guardrails unchanged across templates.

This should be implemented in P21/P22 or dedicated P25 extension.

---

## H) Step-by-step for your next 2 steps

### P20 (now)
- Validate payload schemas
- Ensure error messages are clear
- Block malformed requests early

### P21 (next)
- Build LangGraph nodes:
  - load inputs
  - match/rank
  - generate
  - guardrails
  - approval gate decision
- Persist graph state per run

---

## I) Test protocol before each sync

```bash
scripts/run_phase2_tests.sh
PYTHONPATH=src pytest -q tests/integration/test_phase3_bootstrap_endpoints.py
```

If green:
- create PR
- merge to `phase3-dev`
- periodically merge `phase3-dev` to `main` when stable
