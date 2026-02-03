# 03_Weekly_MVP_Demo_Plan_Week1.md
# CareerOS — Weekly MVP Demo Plan (Week 1) + 2-Week Release Cadence
Project: CareerOS Agentic AI Capstone  
Doc Type: Delivery Plan (Hands-on Demos)  
Version: v1.1 (Feb 2026)

---

## 0) Goal
You will run **3–4 hands-on MVP demos** in class in the next-to-next week.  
Each demo proves a portion of the end-to-end pipeline and produces real artifacts.

---

# 1) Demo pack for next-to-next week (3–4 demos)

## Demo 1 — Intake → Parse → Evidence Graph (Pipeline Start)
### Pipeline slice
F1 → F4 → F5 → F6

### Inputs
- **[USER]** resume.pdf  
- **[USER]** constraints: role target, location/remote, salary band

### Steps
1) Run intake (create `intake_bundle.json`)
2) Store resume as `resume_v1.pdf`
3) Parse resume → `profile.json`
4) Build evidence graph → `evidence_graph.json` + coverage report

### Outputs to show live
- `outputs/intake/intake_bundle.json`
- `outputs/profile/profile.json`
- `outputs/evidence/evidence_graph.json`
- `outputs/evidence/evidence_coverage.json`

### Must-have success criteria
- profile includes extracted skills + roles timeline
- evidence graph shows at least 3 evidence nodes

### Screenshot checklist
- intake bundle constraints
- one evidence node showing claim → proof

---

## Demo 2 — Job Ingestion → Requirements Extraction
### Pipeline slice
F3 → F7

### Inputs
- **[USER]** 3 job posts (paste text)

### Steps
1) Paste job text → save `job_{id}_raw.txt`
2) Extract requirements → `job_{id}_requirements.json`
3) Repeat for 3 jobs

### Outputs to show live
- `outputs/jobs/job_1_raw.txt`
- `outputs/jobs/job_1_requirements.json` (and 2,3)

### Must-have success criteria
- must-have vs nice-to-have present
- seniority signal extracted

### Screenshot checklist
- requirements JSON fields for one job

---

## Demo 3 — Constraint Gate → Hybrid Ranker (Explainability)
### Pipeline slice
F9 → F10 (depends on prior demos)

### Inputs
- `intake_bundle.json`
- job requirements for 3 jobs
- `evidence_graph.json`

### Steps
1) Run constraint gate → `eligibility_report.json`
2) Run ranker → `ranked_jobs.json`
3) explain why job #1 is top

### Outputs to show live
- `outputs/match/eligibility_report.json`
- `outputs/match/ranked_jobs.json`

### Must-have success criteria
- >=1 job rejected with reason
- ranked list includes score breakdown

### Screenshot checklist
- ranked list and breakdown for top 2 jobs

---

## Demo 4 — Generate Bullets/Cover Letter → Validate → Approve → Export
### Pipeline slice
F11 → F12 → F14 → F15 → F16 → F17

### Inputs
- evidence graph + selected job requirements (top job)
- ranked job id

### Steps
1) Generate bullets and cover letter
2) Run claim validator; ensure it blocks at least 1 unsupported claim
3) approve
4) export bundle with audit

### Outputs to show live
- `outputs/gen/resume_bullets_job_{id}.md`
- `outputs/guard/blocked_claims_job_{id}.json`
- `outputs/audit/audit_job_{id}.json`
- `exports/{company}_{role}_{date}/...`

### Must-have success criteria
- 5+ grounded bullets generated
- 1 blocked claim shown
- export bundle created

### Screenshot checklist
- blocked claim
- export folder structure

---

# 2) 2-week cadence plan (3–4 MVPs every 2 weeks)
The rule: every 2 weeks, we must demo something that runs end-to-end for a slice.

## Sprint 1 (Weeks 1–2): Core Proof (this doc)
- 4 demos above

## Sprint 2 (Weeks 3–4): Reliability + Evaluation + Version discipline
- Add evaluation harness for ranking quality (basic metrics)
- Add MLflow tracking for ranker/generator runs
- Improve deterministic scoring + repeatability mode

## Sprint 3 (Weeks 5–6): Clean service boundaries + API
- Split into FastAPI endpoints for each major feature
- Streamlit UI calls API

## Sprint 4 (Weeks 7–8): Docker + CI
- Dockerize backend and UI
- GitHub Actions: tests, lint, build

## Sprint 5 (Weeks 9–10): Monitoring + Quality Controls
- structured logs + basic Grafana dashboard
- Evidently report on ranking feature distributions

## Sprint 6 (Weeks 11–12): Orchestration + Streaming (Optional)
- CrewAI/MCP orchestration toggle
- Kafka events for job ingestion and workflow steps

---

# 3) Deliverables checklist (for Week 1 submission)
- Notebooks:
  - `notebooks/01_intake_parse_evidence.ipynb`
  - `notebooks/02_job_ingest_requirements.ipynb`
  - `notebooks/03_gate_rank_explain.ipynb`
  - `notebooks/04_generate_validate_export.ipynb`
- Output folders:
  - `/outputs/` contains all JSON/MD artifacts
  - `/exports/` contains at least one package folder
- `README_demo.md` with exact run instructions
