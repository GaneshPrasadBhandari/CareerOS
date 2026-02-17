# docs/quality/TEST_STRATEGY.md
# CareerOS — Test Strategy (Unit / Integration / Eval Gates + CI Rules)
Project: CareerOS Agentic AI Capstone  
Owner: Ganesh Prasad Bhandari  
Doc Type: Quality Plan  
Version: v1.0 (Feb 2026)

---

## 0) Quality philosophy
We do not move to the next layer until the current layer:
- produces correct artifacts
- passes unit tests
- passes a minimal integration flow

Rule: **Artifact contracts are the test boundaries.**

---

## 1) Test layers

### 1.1 Unit tests (fast, isolated)
Location: `tests/unit/`  
Scope:
- schema validation (Pydantic)
- parsing functions
- scoring functions
- validator logic
- export naming/versioning logic

Must run in CI on every PR.

### 1.2 Integration tests (end-to-end “happy path”)
Location: `tests/integration/`  
Scope:
- “resume + 3 jobs” produces ranked_jobs.json
- generation produces outputs
- validator blocks at least one unsupported claim in demo fixtures
- export only after approval

Runs in CI (smoke level). Keep runtime low.

### 1.3 Evaluation tests (quality signals)
Location: `tests/eval/` or `evaluation/`  
Scope:
- ranking sanity checks (weights, breakdown fields, stability)
- grounded generation checks (evidence references present)
- drift checks (Evidently reports later)

Runs on schedule or manually (not necessarily on every PR early).

---

## 2) Phase-wise test gates (when to proceed)

### Gate A — Phase 0 complete
- `pytest` runs
- CI green
- lint/format checks pass
- `.env` loading verified

### Gate B — Phase 1 complete (Resume → Evidence)
- profile.json schema valid
- evidence_graph.json has ≥3 nodes
- deterministic mode test passes

### Gate C — Phase 2 complete (Jobs → Rank)
- job_requirements schema valid for 3 jobs
- eligibility report rejects known ineligible job
- ranked_jobs includes score breakdown
- integration happy path passes

### Gate D — Phase 3 complete (Generate → Validate → Approve)
- bullets and letter generated and non-empty
- validator blocks known unsupported claim in fixture
- approval required before export

### Gate E — Phase 4 complete (UI/API + Export)
- full run through API endpoints passes integration test
- export bundle created with audit.json
- no overwrite policy enforced

### Gate F — Phase 5 complete (MLflow/DVC/Docker)
- Docker compose runs full system
- MLflow logs run_id
- DVC reproduces fixtures from clean checkout

### Gate G — Phase 6 complete (Deploy/Monitoring/Eval)
- deployed stack runnable OR containerized demo stable
- Grafana dashboard exists (minimal)
- Evidently report generated at least once

---

## 3) CI/CD rules (GitHub Actions)
On PR:
- install dependencies via `pyproject.toml`
- run lint/format check
- run unit tests
- run integration smoke tests

On merge to main:
- run full test suite
- build Docker images (optional push later)

---

## 4) Test fixtures (golden inputs)
Maintain a small fixed dataset in repo (or DVC-tracked):
- 1 sample resume (redacted if needed)
- 3 sample job posts
- 1 job post designed to fail a constraint
- 1 generation scenario designed to trigger blocked claim

Purpose: reproducible demos + stable CI tests.
