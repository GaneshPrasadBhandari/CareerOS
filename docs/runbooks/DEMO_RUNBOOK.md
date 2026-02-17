# docs/runbooks/DEMO_RUNBOOK.md
# CareerOS — Demo Runbook (Guaranteed End-to-End Demo)
Project: CareerOS Agentic AI Capstone  
Owner: Ganesh Prasad Bhandari  
Doc Type: Demo Execution Script  
Version: v1.0 (Feb 2026)

---

## 0) Demo objective (what we prove)
In one run, CareerOS must produce:
1) ranked shortlist for at least 3 job posts  
2) at least one exported job-specific package  
3) at least one blocked unsupported claim  
4) an audit log explaining ranking + validation  

---

## 1) Pre-demo checklist (5 minutes before)
- `.env` present with API keys
- demo fixtures available:
  - `fixtures/resume_demo.pdf`
  - `fixtures/jobs/job1.txt`, `job2.txt`, `job3.txt`
- `DEMO_MODE=true`
- MLflow running (optional, but recommended)

---

## 2) Demo path A — Streamlit UI (preferred for class)
### Steps
1) Start backend:
   - `uvicorn apps.api.main:app --reload`
2) Start UI:
   - `streamlit run apps/ui/Home.py`
3) Upload resume (fixtures/resume_demo.pdf)
4) Paste 3 job posts (job1, job2, job3)
5) Click “Run Pipeline”
6) Show outputs:
   - eligibility results (at least 1 rejected)
   - ranked shortlist with breakdown
7) Select top job → “Generate”
8) Show blocked claim report (must exist)
9) Approve → Export package
10) Open export folder and show:
   - resume bullets file
   - cover letter file
   - audit.json

### What to say (short script)
- “We start by structuring candidate evidence.”
- “We convert job posts into structured requirements.”
- “We gate by constraints and rank with explainability.”
- “We generate artifacts grounded in evidence.”
- “We block unsupported claims.”
- “We export a versioned package with an audit trail.”

---

## 3) Demo path B — CLI / Script (backup plan)
### Steps
1) Run pipeline command:
   - `python -m careeros.run_demo --resume fixtures/resume_demo.pdf --jobs fixtures/jobs/`
2) Show created artifacts:
   - outputs/profile/profile.json
   - outputs/evidence/evidence_graph.json
   - outputs/match/ranked_jobs.json
   - outputs/guard/blocked_claims_job_{id}.json
   - outputs/audit/audit_job_{id}.json
3) Show export folder:
   - exports/{company}_{role}_{date}/...

---

## 4) Expected artifacts checklist (must exist after demo)
- `outputs/profile/profile.json`
- `outputs/evidence/evidence_graph.json`
- `outputs/jobs/job_1_requirements.json` (and 2,3)
- `outputs/match/eligibility_report.json`
- `outputs/match/ranked_jobs.json`
- `outputs/guard/blocked_claims_job_{id}.json`
- `outputs/audit/audit_job_{id}.json`
- `exports/{company}_{role}_{date}/...`

---

## 5) Screenshot checklist (for class report)
1) Intake constraints screenshot (UI)
2) Evidence graph summary
3) Requirements JSON snippet
4) Ranked shortlist + breakdown
5) Blocked claim report
6) Export folder structure
7) Audit log snippet

---

## 6) If something breaks (fast recovery)
- If UI breaks: use CLI demo path B
- If ranking breaks: show gate + evidence + requirements outputs
- If generation breaks: still demo ranking + explainability + audit
- If validator breaks: show evidence coverage report to prove “trust intent”
