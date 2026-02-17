# 02_MVP_Features_Ranked.md
# CareerOS — MVP Features (Ranked by Value + Sequential Flow)
Project: CareerOS Agentic AI Capstone  
Doc Type: MVP Scope (Features + Artifacts + Demo Criteria)  
Version: v1.1 (Feb 2026)

---

## 0) What MVP means for CareerOS
**MVP = Minimum Viable Proof** that CareerOS can execute the core promise end-to-end:

**Resume + constraints + job posts → ranked shortlist → grounded application artifacts → approval → export bundle with traceability**

If we can do that reliably with real inputs, CareerOS is “real product,” not a chatbot demo.

---

## 1) MVP selection criteria (must satisfy ALL)
A feature is MVP if it:
1) is required for the end-to-end promise  
2) produces a tangible artifact (file/output)  
3) is demo-able in < 10 minutes  
4) reduces major risk (wrong match / hallucination / untraceable output)

---

## 2) MVP features (ranked) with artifact wiring

### MVP-1. F1 Guided Intake Wizard (Value: 5/5)
- **Why MVP:** downstream steps depend on complete constraints + role targets.
- **Inputs:** **[USER]** resume + constraints/preferences  
- **Outputs:**
  - `outputs/intake/intake_bundle.json`
  - `outputs/intake/resume_original.pdf`
- **Downstream consumers:** F4, F5, F9  
- **Demo criteria:** show complete intake bundle with constraints  
- **Success metrics:** intake completion rate, required fields present

---

### MVP-2. F4 Resume Storage + Versioning (Value: 4/5)
- **Why MVP:** reproducibility + safe iteration.
- **Inputs:** **[UPSTREAM]** `resume_original.pdf` (MVP-1)  
- **Outputs:**
  - `artifacts/raw/resume_v1.pdf`
  - `outputs/intake/resume_hash.json`
- **Downstream consumers:** F5, F16  
- **Demo criteria:** show resume_v1 exists; upload v2 if needed  
- **Success metrics:** version retrieval success

---

### MVP-3. F5 Resume Parser → Profile JSON (Value: 5/5)
- **Why MVP:** structured profile is the foundation for evidence + ranking.
- **Inputs:**
  - **[UPSTREAM]** `resume_v1.pdf` (MVP-2)
  - **[UPSTREAM]** `intake_bundle.json` (MVP-1)
- **Outputs:** `outputs/profile/profile.json`  
- **Downstream consumers:** F6, F10  
- **Demo criteria:** open `profile.json` and show skills/experience extracted  
- **Success metrics:** completeness (% skills/roles extracted)

---

### MVP-4. F6 Evidence Graph Builder (Value: 5/5)
- **Why MVP:** enables “no evidence, no claim” and trustworthy generation.
- **Inputs:**
  - **[UPSTREAM]** `profile.json` (MVP-3)
  - **[USER]** optional project snippets/links (via intake_bundle)
- **Outputs:**
  - `outputs/evidence/evidence_graph.json`
  - `outputs/evidence/evidence_coverage.json`
- **Downstream consumers:** F10, F11, F12, F14  
- **Demo criteria:** show at least 3 evidence nodes + coverage report  
- **Success metrics:** evidence coverage %, unsupported claims list

---

### MVP-5. F3 Job Post Ingestion (Paste URL/Text) (Value: 5/5)
- **Why MVP:** job post normalization is required for requirements extraction.
- **Inputs:** **[USER]** job text/URL  
- **Outputs:** `outputs/jobs/job_{id}_raw.txt`  
- **Downstream consumers:** F7  
- **Demo criteria:** ingest 3 job posts  
- **Success metrics:** ingestion success rate

---

### MVP-6. F7 Job Requirements Extractor (Value: 5/5)
- **Why MVP:** converts raw job text to structured requirements used by gate/ranker/generator.
- **Inputs:** **[UPSTREAM]** `job_{id}_raw.txt` (MVP-5)  
- **Outputs:** `outputs/jobs/job_{id}_requirements.json`  
- **Downstream consumers:** F9, F10, F11, F12  
- **Demo criteria:** show must-have vs nice-to-have fields  
- **Success metrics:** human agreement (manual check in capstone)

---

### MVP-7. F9 Constraint Gate (Hard Filters) (Value: 5/5)
- **Why MVP:** removes irrelevant jobs early and increases trust.
- **Inputs:**
  - **[UPSTREAM]** constraints from `intake_bundle.json` (MVP-1)
  - **[UPSTREAM]** `job_{id}_requirements.json` (MVP-6)
- **Outputs:** `outputs/match/eligibility_report.json`  
- **Downstream consumers:** F10  
- **Demo criteria:** show at least one job rejected with reason  
- **Success metrics:** irrelevant jobs reduced, clarity of reasons

---

### MVP-8. F10 Hybrid Ranker v1 (Value: 5/5)
- **Why MVP:** shortlist quality is the core product value.
- **Inputs:**
  - **[UPSTREAM]** `evidence_graph.json` (MVP-4)
  - **[UPSTREAM]** `job_{id}_requirements.json` (MVP-6)
  - **[UPSTREAM]** `eligibility_report.json` (MVP-7)
- **Outputs:** `outputs/match/ranked_jobs.json` (includes score breakdown)  
- **Downstream consumers:** F11, F12, F16, UI explain view  
- **Demo criteria:** show top 5 jobs with score breakdown  
- **Success metrics:** top-3 acceptance, consistency across reruns

---

### MVP-9. F11 Evidence-backed Resume Bullets Generator (Value: 5/5)
- **Why MVP:** tangible artifact users want + strong demo.
- **Inputs:**
  - **[UPSTREAM]** evidence graph (MVP-4)
  - **[UPSTREAM]** job requirements (MVP-6)
  - **[UPSTREAM]** selected job id from ranked_jobs (MVP-8)
- **Outputs:**
  - `outputs/gen/resume_bullets_job_{id}.md`
  - `outputs/gen/resume_bullets_job_{id}.json`
- **Downstream consumers:** F14, F17  
- **Demo criteria:** generate 5+ bullets that map to evidence ids  
- **Success metrics:** unsupported claim leakage rate near 0

---

### MVP-10. F12 Grounded Cover Letter Generator (Value: 4/5)
- **Why MVP:** completes the “package” story.
- **Inputs:** same as MVP-9  
- **Outputs:** `outputs/gen/cover_letter_job_{id}.md`  
- **Downstream consumers:** F14, F17  
- **Demo criteria:** 3–4 paragraphs referencing evidence  
- **Success metrics:** user edit reduction (qualitative for now)

---

### MVP-11. F14 Claim Validator (Value: 5/5)
- **Why MVP:** prevents hallucination; differentiates CareerOS from generic GenAI tools.
- **Inputs:**
  - **[UPSTREAM]** generated artifacts (MVP-9/MVP-10)
  - **[UPSTREAM]** evidence graph (MVP-4)
- **Outputs:**
  - `outputs/guard/validated_resume_bullets_job_{id}.md`
  - `outputs/guard/validated_cover_letter_job_{id}.md`
  - `outputs/guard/blocked_claims_job_{id}.json`
- **Downstream consumers:** F15, F16, F17  
- **Demo criteria:** force 1 blocked claim and show it  
- **Success metrics:** hallucination leakage rate ~0

---

### MVP-12. F15 Human Approval Gate (Value: 5/5)
- **Why MVP:** ensures user control and safe export.
- **Inputs:** **[UPSTREAM]** validated artifacts (MVP-11)  
- **Outputs:** `outputs/guard/approval_job_{id}.json`  
- **Downstream consumers:** F17  
- **Demo criteria:** approval checkbox required before export  
- **Success metrics:** no export without approval

---

### MVP-13. F16 Lightweight Audit Log (Value: 4/5)
- **Why MVP:** makes outputs defensible in class and reproducible.
- **Inputs:**
  - **[UPSTREAM]** ranked_jobs.json (MVP-8)
  - **[UPSTREAM]** eligibility_report.json (MVP-7)
  - **[UPSTREAM]** blocked_claims.json (MVP-11)
  - **[SYSTEM]** run_id, timestamps
- **Outputs:** `outputs/audit/audit_job_{id}.json`  
- **Downstream consumers:** explain-my-rank view, evaluation later  
- **Demo criteria:** open audit and explain why job ranked #1  
- **Success metrics:** “explain in 60 seconds” test

---

### MVP-14. F17 Export Package Builder (Value: 5/5)
- **Why MVP:** gives the user a final usable bundle (product feel).
- **Inputs:**
  - **[UPSTREAM]** approval_job_{id}.json (MVP-12)
  - **[UPSTREAM]** validated artifacts (MVP-11)
  - **[UPSTREAM]** audit_job_{id}.json (MVP-13)
- **Outputs:**
  - `exports/{company}_{role}_{date}/resume_v1.md`
  - `exports/{company}_{role}_{date}/cover_letter_v1.md`
  - `exports/{company}_{role}_{date}/audit.json`
- **Downstream consumers:** user  
- **Demo criteria:** show export folder created with correct structure  
- **Success metrics:** export success + consistent naming

---

## 3) MVP end-to-end flow (one-line wiring)
F1 → F4 → F5 → F6 → (F3 → F7) → F9 → F10 → (F11 + F12) → F14 → F15 → F16 → F17

---

## 4) MVP “definition of done” (for capstone)
MVP is done when:
- 1 resume + 3 job posts can be processed end-to-end
- ranked shortlist is generated with reasons
- at least one job package can be exported
- claim validator blocks unsupported claims
- audit log exists for that package
