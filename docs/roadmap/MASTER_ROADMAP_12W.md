# docs/roadmap/MASTER_ROADMAP_12W.md
# CareerOS — MASTER ROADMAP (12 Weeks / 3 Months)
Project: CareerOS Agentic AI Capstone  
Owner: Ganesh Prasad Bhandari  
Doc Type: Master Execution Roadmap (Phases + Exit Gates + Demo Cadence)  
Version: v1.0 (Feb 2026)

---

## 0) BLUF
In 12 weeks, CareerOS will ship a deployed, working product that:
- ingests resume + constraints + job posts
- produces an explainable ranked shortlist
- generates grounded bullets + cover letter
- blocks unsupported claims
- requires human approval before export
- exports a versioned job package with an audit trail
- runs with CI/CD, tests, MLflow tracking, and DVC versioning
- is containerized (Docker) and optionally deployable to Kubernetes
- includes basic monitoring (Grafana) and evaluation/drift reports (Evidently)

Core principle: **Every layer produces artifacts. Every artifact has tests.**  
Agents are added only after contracts are stable.

---

## 1) Operating model (how we build)
### 1.1 Two-week demo cadence
Every 2 weeks, we deliver a demoable vertical slice:
- Sprint 1 (Weeks 1–2): Resume → Evidence Graph + Job → Requirements
- Sprint 2 (Weeks 3–4): Gate + Rank + Explain
- Sprint 3 (Weeks 5–6): Generate + Validate + Export
- Sprint 4 (Weeks 7–8): API+UI integration + Integration tests
- Sprint 5 (Weeks 9–10): MLflow+DVC + CI/CD gates + Docker
- Sprint 6 (Weeks 11–12): Deploy + Monitoring + Evaluation + Agent mode toggle (if stable)

### 1.2 Build strategy (notebook-first, then modular)
- Prototype each new layer in `/notebooks/`
- Freeze output artifacts + schemas
- Move into modular Python under `/src/`
- Add tests before moving to next layer

### 1.3 Governance strategy (trust-first)
- Evidence Graph is mandatory
- Generators must cite evidence ids
- Claim Validator blocks unsupported claims
- Human Approval Gate blocks export unless approved
- Audit log ties everything together

---

## 2) Phase 0 (Week 1) — Product Rails Setup (Non-negotiable)
**Goal:** engineering foundation that supports fast iteration and safe releases.

### Build steps
1. VS Code workspace + Python environment + basic tooling
2. GitHub repo sync + branch policy (main/dev/feature branches)
3. Project skeleton with `pyproject.toml` (src-layout), logging, exceptions
4. `.env` + Pydantic settings for API keys and runtime config
5. `pytest` harness (unit + integration folders)
6. GitHub Actions CI: lint + unit tests + integration smoke
7. MLflow local tracking (runs + config)
8. DVC initialized (track sample artifacts/test fixtures)

### Deliverables
- Repo structure + README
- `pyproject.toml`, `.env.example`, `.gitignore`, pre-commit config
- CI pipeline passing on PR
- MLflow running locally
- DVC initialized with at least one tracked sample

### Exit gate (must pass)
- `pytest` passes locally
- CI passes on PR
- `.env` loads correctly; no secrets committed
- MLflow run is created for a smoke pipeline run
- DVC status clean + tracked sample exists

### Demo checkpoint
- Show repo runs, tests pass, CI green, MLflow UI shows a run

---

## 3) Phase 1 (Weeks 2–3) — L1–L3 Core Spine (Resume → Evidence)
**Goal:** build the “truth layer” that prevents hallucinations.

### Build steps (notebook → modular)
1. L1 Intake: capture resume + constraints + targets → `intake_bundle.json`
2. L2 Storage: versioned resume artifact (`resume_v1`) + hash
3. L3 Resume Parser → `profile.json` (skills, roles, timeline, projects)
4. L3 Evidence Graph Builder → `evidence_graph.json` + `evidence_coverage.json`
5. Convert notebooks into modules:
   - `src/intake/`
   - `src/parsing/`
   - `src/evidence/`

### Deliverables
- `outputs/intake/intake_bundle.json`
- `artifacts/raw/resume_v1.pdf`
- `outputs/profile/profile.json`
- `outputs/evidence/evidence_graph.json`
- `outputs/evidence/evidence_coverage.json`

### Tests (minimum)
- Schema validation tests (Pydantic models)
- Deterministic mode test: same input → same output
- Evidence coverage test: unsupported claims surfaced

### Exit gate (must pass)
- One command produces profile + evidence artifacts
- Evidence graph has ≥3 evidence nodes
- Unit tests pass and are stable
- MLflow logs run_id + key artifact paths

### Demo checkpoint (end of Week 3)
- Upload resume → show profile + evidence graph + coverage report

---

## 4) Phase 2 (Weeks 4–5) — L2/L4 Job Intelligence + L5 Gate/Rank (Jobs → Shortlist)
**Goal:** structured job understanding and explainable ranking.

### Build steps
1. L2 Job Ingestion (paste-first) → `job_{id}_raw.txt`
2. L4 Requirements Extractor → `job_{id}_requirements.json`
3. L5 Constraint Gate → `eligibility_report.json` (reasons included)
4. L5 Hybrid Ranker v1 → `ranked_jobs.json` (score breakdown per job)
5. Convert notebooks into modules:
   - `src/jobs/`
   - `src/matching/`

### Deliverables
- `outputs/jobs/job_{id}_raw.txt`
- `outputs/jobs/job_{id}_requirements.json`
- `outputs/match/eligibility_report.json`
- `outputs/match/ranked_jobs.json`

### Tests + basic eval
- Requirements schema tests (must-have/nice-to-have always present)
- Constraint gate tests (known jobs rejected correctly)
- Ranker determinism test (same inputs → same rank in deterministic mode)
- Basic ranking sanity: weights sum to 1, score breakdown present

### Exit gate (must pass)
- 3 jobs in → ranked shortlist out
- At least 1 job rejected with reason (test case)
- Integration “happy path” works locally (CLI or notebook)
- CI green

### Demo checkpoint (end of Week 5)
- Paste 3 jobs → show eligibility + ranked shortlist + breakdown

---

## 5) Phase 3 (Weeks 6–7) — L6 Generation + L7 Guardrails (Artifacts without lies)
**Goal:** generate deliverables safely and enforce trust gates.

### Build steps
1. L6 Bullets Generator (must embed evidence ids)
2. L6 Cover Letter Generator (grounded in evidence + requirements)
3. L7 Claim Validator → blocks unsupported claims
4. L7 Human Approval Gate → export only after approval
5. Add audit context capture (inputs/outputs references)

### Deliverables
- `outputs/gen/resume_bullets_job_{id}.md`
- `outputs/gen/cover_letter_job_{id}.md`
- `outputs/guard/blocked_claims_job_{id}.json`
- `outputs/guard/validated_*` artifacts
- `outputs/guard/approval_job_{id}.json`

### Tests + eval
- Validator tests: known unsupported claim must be blocked
- “No export without approval” test
- Generator formatting sanity tests
- Evidence linkage test: bullets reference evidence ids

### Exit gate (must pass)
- Generates ≥5 grounded bullets for top job
- Blocks at least 1 unsupported claim (intentional test)
- Approval required to proceed
- Audit capture ready

### Demo checkpoint (end of Week 7)
- Generate → validate → show blocked claim → approve (but export comes next phase)

---

## 6) Phase 4 (Weeks 8–9) — L8 Packaging + L1 UI + API Separation (Product feel)
**Goal:** turn the pipeline into a usable application with API/UI.

### Build steps
1. L8 Package Builder → exports folder per job + versioned files
2. L7 Audit Log → ties rank + validation + inputs in `audit.json`
3. FastAPI endpoints for pipeline steps (contract layer)
4. Streamlit UI (thin UI calling API):
   - upload resume
   - paste job posts
   - run pipeline
   - view ranked shortlist + reasons
   - generate + validate + approve + export

### Deliverables
- `exports/{company}_{role}_{date}/...`
- `outputs/audit/audit_job_{id}.json`
- `apps/api/` (FastAPI)
- `apps/ui/` (Streamlit)

### Tests
- Integration tests: API “happy path”
- UI smoke test (manual checklist)
- Export versioning test (no overwrite)

### Exit gate (must pass)
- Full end-to-end run through UI produces export bundle + audit
- Integration tests pass in CI
- No overwrite policy enforced

### Demo checkpoint (end of Week 9)
- Full product demo through Streamlit: resume + 3 jobs → export package

---

## 7) Phase 5 (Weeks 10–11) — MLflow + DVC + CI/CD + Docker (Engineering maturity)
**Goal:** make it reproducible, shippable, and credible as a real product.

### Build steps
1. MLflow logging for:
   - ranker weights/config
   - model/prompt versions
   - evaluation metrics
   - artifact paths
2. DVC for:
   - sample resumes/jobs datasets
   - test fixtures (“golden runs”)
3. CI/CD gates in GitHub Actions:
   - unit + integration + lint
   - optional coverage threshold
4. Dockerization:
   - Dockerfile for API
   - Dockerfile for UI
   - docker-compose for local full stack

### Deliverables
- MLflow run history for pipeline runs
- DVC tracked sample datasets + repro commands
- CI pipeline hardened
- `docker-compose.yml` runs full system

### Exit gate (must pass)
- `docker compose up` runs end-to-end
- MLflow logs appear for each run
- CI green on PR + main
- DVC can reproduce sample artifacts from clean checkout

### Demo checkpoint (end of Week 11)
- Run via Docker Compose + show MLflow run + artifacts

---

## 8) Phase 6 (Week 12) — Deploy + Monitoring + Evaluation + Agent Mode Toggle (Optional)
**Goal:** deployment and operational proof; agentic orchestration as controlled enhancement.

### Build steps
1. Deployment target:
   - Local K8s (kind/minikube) OR simple cloud (only if free/available)
2. Observability:
   - structured logs
   - basic metrics endpoint
   - Grafana dashboard (minimal)
3. Evaluation/Drift:
   - Evidently report for ranking score distributions + input drift proxies
4. Agentic orchestration (controlled):
   - pipeline mode (default)
   - agent mode (CrewAI or MCP) as toggle
   - agents operate ONLY via artifact contracts

### Deliverables
- `k8s/` manifests (optional but recommended)
- Grafana dashboard JSON (or config)
- Evidently report artifacts
- Agent mode toggle documented

### Exit gate (must pass)
- deployed or containerized system demonstrably runnable
- monitoring/eval artifacts generated at least once
- agent mode does not break governance guarantees

### Final demo (Week 12)
- “Seminar-grade” demo: end-to-end run + audit + blocked claim + MLflow run + monitoring snapshot

---

## 9) Week-by-week checklist (quick view)
- Week 1: Phase 0 complete (rails + CI + MLflow + DVC baseline)
- Weeks 2–3: Phase 1 (resume → evidence) demo
- Weeks 4–5: Phase 2 (jobs → shortlist) demo
- Weeks 6–7: Phase 3 (generate + validate + approve) demo
- Weeks 8–9: Phase 4 (UI+API + export + audit) demo
- Weeks 10–11: Phase 5 (MLflow/DVC/CI + Docker) demo
- Week 12: Phase 6 (deploy + monitoring + evaluation + optional agents) final demo

---

## 10) Non-negotiables (success rules)
1. Artifact-first design: every layer writes outputs that downstream consumes
2. Test gates: no moving forward without passing tests
3. Governance enforced at runtime: validator + approval gate
4. Deterministic mode for demos
5. No secret keys in repo, ever
