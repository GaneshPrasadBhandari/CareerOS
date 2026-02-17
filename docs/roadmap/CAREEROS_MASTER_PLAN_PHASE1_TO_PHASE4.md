# CareerOS — Master Plan (Phase 1 → Phase 4)  
**Author:** Ganesh Prasad Bhandari  
**Project:** CareerOS (Capstone → Portfolio → Startup Product)

---

## 0) Why this master plan exists
I’m building CareerOS as a real product, not a demo. The only way to do that without ending up with fragile “agent chaos” is to build a deterministic spine first (artifact contracts + tests + audit trail), and only then layer in LLMs, RAG, agent orchestration, and automation.

This document is my single source of truth for:
- what I already built (Phase 1)
- what I’m building next (Phase 2)
- what comes after (Phase 3 and Phase 4)
- how pipeline steps map to the 9-layer architecture, so there’s zero confusion

---

## 1) Two numbering systems (this is the common confusion)
CareerOS uses **two valid but different** structures:

### A) Architecture Layers (L1–L9) — what the product is
These match the architecture diagram (Entry/UI → Orchestrator → Managers → Agents → Approvals → Execution → Analytics → Memory/Models → Governance/Ops).

### B) Build Pipeline Steps (P1–P12…) — how I built it in code
These are incremental deliverables that produce artifacts and prove the end-to-end flow.

✅ **Rule:** One pipeline step can map to multiple architecture layers because a single deliverable may touch UI, API, policies, logs, and storage.

---

## 2) Architecture Layers (L1–L9) — what each layer means
### L1 — Entry / UX Layer  
Streamlit UI, intake forms, approvals UI, dashboards.

### L2 — Backend API Layer  
FastAPI endpoints, request validation, routing to services.

### L3 — Orchestration Core  
Planner/Director behavior.  
- Phase 1: deterministic orchestrator runner (pipeline execution)  
- Phase 3: LangGraph-based orchestration + state machine

### L4 — Agent Layer  
Worker capabilities (job understanding, matching, tailoring, cover letters, answers).  
- Phase 1: deterministic functions that behave like agents  
- Phase 2+: real agent tools + LLM + RAG grounding

### L5 — Human Approval Gates  
Approve shortlist, approve package, approve sensitive actions.

### L6 — Execution & Tracking  
Export, tracking ledger, follow-ups, lifecycle transitions.

### L7 — Analytics & Learning  
Funnel metrics, conversion rates, A/B experiments, learning signals.

### L8 — Memory & Models  
Relational DB + vector DB + embeddings + LLM providers/models.

### L9 — Governance / Explainability / Ops  
Audit logs, guardrails, policy enforcement, CI/CD/MLOps hooks, monitoring.

---

## 3) Phase model (the engineering strategy)
### Phase 1 — Deterministic spine (Completed: P1–P12)
No agents, no LLMs, no ML models, no RAG, no vector DB, no auto-apply, no auto-sending emails.  
Everything is deterministic, testable, reproducible, and demo-safe.

### Phase 2 — Grounded reasoning (LLM + RAG) with explicit approval gates
I keep the same artifact contracts and endpoints. I only upgrade the internals to be grounded and explainable.

### Phase 3 — Real agent orchestration (LangGraph-first, MCP-ready)
Once grounding and policies are strong, I introduce an orchestration layer that routes tasks across agents with state, retries, and human approvals.

### Phase 4 — Product-grade engineering (CI/CD, Docker/K8s, Observability, Drift, MLOps)
This turns the system into a deployable, monitorable, portfolio-grade product and sets up the path to monetization later.

---

## 4) Phase 1 (P1–P12): what I built and how it maps to L1–L9
**Phase 1 goal:** prove a complete end-to-end workflow with artifacts, auditability, and guardrails — without AI/LLMs.

### Phase 1 MVP demo proof (must work every time)
In one run, CareerOS produces:
- ranked shortlist for at least 3 job posts
- at least one job-specific application package export
- at least one blocked unsupported claim (guardrail proof)
- audit trail: logs + artifacts + tracking + explainable ranking

---

### P1 — Repo + environment + skeleton + standards
**Maps to:** L9  
**What it is:** project structure, `pyproject.toml`, test folders, logs/outputs/artifacts folders, `.env/.env.example`, hardened `.gitignore`.  
**Why it matters:** prevents chaos and creates a professional engineering baseline.

---

### P2 — Intake Bundle (candidate constraints + targets)
**Maps to:** L1, L2, L9  
**Inputs:** user form fields (roles, location, salary band, authorization, etc.)  
**Outputs:** `outputs/intake/intake_bundle_v1_*.json`  
**Why it matters:** constraints are explicit and stable; downstream steps can’t “guess”.

---

### P3 — Resume Parsing → EvidenceProfile (structured truth)
**Maps to:** L2, L4 (simulated), L9  
**Inputs:** pasted resume text  
**Outputs:** `outputs/profile/profile_v1_*.json`  
**Why it matters:** this becomes the “source of truth” for supported claims later.

---

### P4 — Job Ingestion → JobPost artifacts (paste-first)
**Maps to:** L1, L2, L4 (simulated)  
**Inputs:** pasted job text (3+ posts)  
**Outputs:** `outputs/jobs/job_post_v1_*.json`  
**Why it matters:** job descriptions become clean structured inputs for matching/ranking.

---

### P5 — Matching + Ranking (deterministic, explainable)
**Maps to:** L4 (simulated matching agent), L7 (ranking output), L9 (explainability)  
**Inputs:** EvidenceProfile + JobPosts  
**Outputs:** `outputs/matching/shortlist_v1_*.json` (or equivalent ranking artifact path)  
**Why it matters:** produces a top-N list with reasons (not a black box).

---

### P6 — Application Package generation (deterministic template)
**Maps to:** L4 (simulated tailoring agents), L6 (package readiness), L9  
**Inputs:** EvidenceProfile + JobPost + shortlist context  
**Outputs:** `exports/packages/application_package_v1_*.json`  
**Why it matters:** I can generate a package reliably before introducing “creative” models.

---

### P7 — Guardrails validation (block unsupported claims)
**Maps to:** L9 (governance), L5 (approval escalation), touches L4  
**Inputs:** EvidenceProfile + ApplicationPackage  
**Outputs:** `outputs/guardrails/validation_report_v1_*.json`  
**Policy baseline:** block only when a known tool/tech term is not in EvidenceProfile.skills  
**Why it matters:** this is the “anti-hallucination” proof for the MVP.

---

### P8 — Export + Apply Tracking (DOCX/PDF + ledger)
**Maps to:** L6, L9, touches L5  
**Inputs:** validated package (must pass P7)  
**Outputs:**
- `exports/submissions/<application_id>_<job_hint>/application_package.docx`
- `exports/submissions/<application_id>_<job_hint>/application_package.pdf`
- `outputs/apply_tracking/applications_v1.jsonl`
**Why it matters:** output becomes real-world deliverables + lifecycle state.

---

### P9 — Analytics dashboard (funnel + drilldown)
**Maps to:** L7, L6, L9  
**Inputs:** tracking ledger JSONL  
**Outputs:** API endpoints + Streamlit table + metrics + drilldown  
**Why it matters:** turns CareerOS into an operational product, not a single-run script.

---

### P10 — Next actions queue (follow-ups generator)
**Maps to:** L6, L7, L9  
**Inputs:** tracking ledger  
**Outputs:** `outputs/followups/followups_v1.json`  
**Why it matters:** introduces safe ops automation (no external execution yet).

---

### P11 — Notification drafts (email + LinkedIn, no sending)
**Maps to:** L6, L7, L9, touches L5  
**Inputs:** follow-ups + tracking ledger  
**Outputs:** `outputs/notifications/drafts_v1.json`  
**Why it matters:** converts “actions” into real comms artifacts that can be approved.

---

### P12 — Orchestrator runner (one-click deterministic workflow)
**Maps to:** L3 (orchestration behavior), L6, L9  
**Inputs:** artifact paths + run context  
**Process:** P6 → P7 (stop if blocked) → P8 → P10 → P11  
**Outputs:** single run object containing run_id, status, and artifact paths  
**Why it matters:** this becomes the stable spine that agents will call later as tools.

---

## 5) Phase 2: Grounded LLM + RAG + approvals (no risky automation)
**Phase 2 goal:** upgrade reasoning and output quality while keeping the pipeline stable and safe.

### What I add in Phase 2
1) **RAG evidence store (local-first)**
- chunk resume + project evidence
- embed and store in vector DB
- retrieval returns evidence chunks for any claim

2) **LLM job understanding (structured)**
- job post → must-have / nice-to-have / responsibilities
- always returns JSON + confidence

3) **Hybrid matching**
- constraints gate (location/salary/auth)
- semantic similarity (embeddings)
- evidence coverage score

4) **Evidence-cited generation**
- generated bullets/letters include evidence pointers (chunk ids)
- no citations → lower confidence → route to approval

5) **Guardrails v2**
- claim extraction + evidence lookup
- block unverifiable claims
- warn on low-confidence claims

### What I will NOT do in Phase 2 (defer to Phase 3)
To stay safe and free while still building credibility:
- no full auto-apply to job boards
- no automatic email sending
- no scraping at scale
- no heavy cloud infra unless credits exist

### Phase 2 pipeline extensions (P13–P18)
- **P13:** vector store + embeddings (Chroma/FAISS local)  
- **P14:** LLM adapter + prompt registry + versioning  
- **P15:** job requirements extractor (JSON output)  
- **P16:** hybrid matching v2 (semantic + constraints + evidence)  
- **P17:** grounded generation v2 (citations required)  
- **P18:** guardrails v2 + approval routing state

---

## 6) Phase 3: Real agentic orchestration (LangGraph-first, MCP-ready)
**Phase 3 goal:** introduce real agent orchestration once grounding and policy are strong.

### Why Phase 3 is separate
Agents without strong contracts create:
- unstable demos
- unpredictable tool calls
- hard debugging
- hallucination risk

Phase 3 happens only after the Phase 2 evidence chain is working.

### Orchestration choice (portfolio + market signal)
**LangGraph-first** as the orchestration spine:
- looks like real enterprise workflow graphs
- strong state control, retries, tool boundaries, and approvals
- maps cleanly to “Planner/Director” architecture

**MCP-ready** tool layer:
- stable tool interfaces that agents call
- makes the system modular even if the agent framework changes

CrewAI can still be used later as a lightweight multi-agent simulation, but for MNC/FAANG-style hiring signals, a graph/state-machine orchestrator reads more “production”.

### Phase 3 pipeline steps (P19–P24)
- **P19:** typed global state (Pydantic) for orchestration  
- **P20:** agent contracts (inputs/outputs + artifact writers)  
- **P21:** LangGraph workflow (nodes for each major step)  
- **P22:** explicit human approval nodes (shortlist/package/sensitive actions)  
- **P23:** memory upgrade (SQLite → optional Postgres; vector store persisted)  
- **P24:** evaluation harness (golden runs + regression checks)

---

## 7) Phase 4: Product-grade engineering (CI/CD, Docker/K8s, Monitoring, Drift, MLOps)
**Phase 4 goal:** make CareerOS deployable, observable, and credible as a production build.

### What I implement in Phase 4
- CI/CD gates
- containerization
- deployment path (local → docker compose → minikube)
- metrics + dashboards
- drift monitoring + evaluation reports
- experiment tracking + data versioning

### Phase 4 pipeline steps (P25–P32)
- **P25:** GitHub Actions (lint + unit + integration + golden runs)  
- **P26:** MLflow tracking (ranker configs, prompts, eval metrics)  
- **P27:** DVC (sample datasets + golden outputs)  
- **P28:** Docker Compose (api + ui + vector store + db optional)  
- **P29:** Kubernetes (minikube manifests + ingress)  
- **P30:** monitoring hooks (logs + metrics endpoint + Grafana)  
- **P31:** drift/eval (Evidently reports, score distribution drift)  
- **P32:** release-grade demo runbook (repeatable seminar script)

---

## 8) Free resources strategy (so I don’t accidentally pay for anything)
I follow a strict order:
1) **Local-first defaults**
- Chroma/FAISS locally
- sentence-transformers embeddings locally
- optional local LLM (if needed)

2) **Use existing accounts**
- GitHub Actions
- Hugging Face (if already active)

3) **Create new accounts only if required**
- OpenAI/Azure OpenAI only when it unlocks a Phase 2 milestone
- search APIs (Serper/Tavily/etc.) only if I move beyond paste-first job inputs

**All external calls are feature-flagged** and disabled by default.

---

## 9) Current checkpoint (where I am right now)
✅ Phase 1 (P1–P12) deterministic spine exists and is demoable.  
➡️ Next milestone: Phase 2 starts with **P13 (RAG evidence store)** because that unlocks grounded LLM work without rewriting the pipeline.

---

## 10) Next steps (the non-confusing order I’ll follow)
1) Finish P12 testing and create a release tag: `phase1-deterministic-spine`  
2) Start Phase 2 with P13 (resume/job chunking + embeddings + vector store)  
3) Add P14 prompt registry + LLM adapter (feature-flagged)  
4) Upgrade P15–P18 one by one (requirements → hybrid match → grounded generation → guardrails v2)  
5) Only then begin Phase 3 orchestration (LangGraph + MCP-ready tools)  
6) Finish with Phase 4 production engineering (CI/CD, Docker, K8s, Monitoring, Drift, MLOps)

