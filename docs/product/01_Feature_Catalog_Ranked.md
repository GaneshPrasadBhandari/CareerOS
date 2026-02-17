# 01_Feature_Catalog_Ranked.md
# CareerOS — Feature Catalog (Ranked by Value)
Project: CareerOS Agentic AI Capstone  
Doc Type: Product Feature Catalog  
Version: v1.1 (Feb 2026)

---

## 0) How to read this document
This catalog lists **all CareerOS features** derived from the architecture and organized **stagewise across 9 layers**.

Key idea: **Every feature produces an output artifact.**  
That artifact becomes the **input** for downstream layers.  
So you can follow the system like a pipeline:

**User Inputs → Intake Bundle → Parsed Profile → Evidence Graph → Job Requirements → Eligibility → Ranking → Generated Artifacts → Validation → Export Bundle → Logs/Evaluation**

### Notation used
- **Input Sources**
  - **[USER]**: provided directly by user (resume/job text/preferences)
  - **[UPSTREAM]**: output coming from a prior feature/layer
  - **[SYSTEM]**: configuration/runtime state/logging

- **Artifacts naming convention (default)**
  - `outputs/intake/intake_bundle.json`
  - `outputs/profile/profile.json`
  - `outputs/evidence/evidence_graph.json`
  - `outputs/jobs/job_{id}_raw.txt`
  - `outputs/jobs/job_{id}_requirements.json`
  - `outputs/match/eligibility_report.json`
  - `outputs/match/ranked_jobs.json`
  - `outputs/gen/resume_bullets_job_{id}.md`
  - `outputs/gen/cover_letter_job_{id}.md`
  - `outputs/guard/blocked_claims_job_{id}.json`
  - `exports/{company}_{role}_{date}/...`
  - `outputs/audit/audit_job_{id}.json`

---

# 1) CareerOS 9 Layers
1. **L1 — User & UX Layer**  
2. **L2 — Input & Connectors Layer**  
3. **L3 — Parsing + Evidence Graph Layer**  
4. **L4 — Knowledge + Retrieval (RAG) Layer**  
5. **L5 — Matching + Ranking (ML/Rules) Layer**  
6. **L6 — Generation (LLM) Layer**  
7. **L7 — Guardrails + Governance Layer**  
8. **L8 — Workflow + Packaging Layer**  
9. **L9 — Platform Ops (MLOps, CI/CD, Observability) Layer**

---

# 2) Stagewise Feature Catalog (with sequential inputs/outputs)

## L1 — User & UX Layer

### F1. Guided Intake Wizard (Value: 4/5)
- **Layer / Stage:** L1  
- **Problem:** Users provide incomplete context; downstream ranking/generation becomes unreliable.  
- **Inputs:**
  - **[USER]** resume PDF/DOCX (required)
  - **[USER]** job search preferences (role, location, remote/hybrid, salary band)
  - **[USER]** constraints (visa/work auth notes, availability)
  - **[USER]** LinkedIn URL / GitHub links (optional)
- **Processing:** guided steps + validation (required fields, format checks)  
- **Outputs (Artifacts):**
  - `outputs/intake/intake_bundle.json`
  - `outputs/intake/resume_original.pdf` (stored copy)
- **Downstream consumer (who uses this output):**
  - **F4 Resume Storage** (L2)
  - **F5 Resume Parser** (L3)
  - **F9 Constraint Gate** (L5) uses constraints/preferences from intake_bundle
- **Success metrics:** intake completion %, missing field reduction  
- **Demo example:** user selects “Remote only” + “Data Scientist / GenAI” + salary band  
- **Dependencies:** none  
- **Risks/Notes:** MVP can be Streamlit form + JSON output.

### F2. Explain-My-Rank View (Value: 5/5)
- **Layer / Stage:** L1  
- **Problem:** Users won’t trust ranking without reasons and evidence.  
- **Inputs:**
  - **[UPSTREAM]** `outputs/match/ranked_jobs.json` (from F10)
  - **[UPSTREAM]** `outputs/audit/audit_job_{id}.json` (from F16)
- **Processing:** render score breakdown + evidence pointers  
- **Outputs (Artifacts):**
  - UI view (no file required), optional `outputs/ui/rank_explain_{id}.md`
- **Downstream consumer:** not required; this is a presentation feature  
- **Success metrics:** user trust rating, top-3 selection from top-10  
- **Dependencies:** F10, F16

---

## L2 — Input & Connectors Layer

### F3. Job Post Ingestion (Paste URL/Text) (Value: 5/5)
- **Layer / Stage:** L2  
- **Problem:** Job posts come in messy formats; we need normalized text.  
- **Inputs:**
  - **[USER]** job description pasted OR job URL  
  - **[SYSTEM]** fetch mode = paste-first (MVP) or fetch-url (v2)
- **Processing:** normalize text (strip HTML, remove nav garbage if URL)  
- **Outputs (Artifacts):**
  - `outputs/jobs/job_{id}_raw.txt`
- **Downstream consumer:**
  - **F7 Job Requirements Extractor** (L4)
- **Success metrics:** % jobs successfully normalized  
- **Dependencies:** none (paste-first avoids scraper complexity)

### F4. Resume Upload Storage + Versioning (Value: 4/5)
- **Layer / Stage:** L2  
- **Problem:** Need durable artifacts + version history.  
- **Inputs:**
  - **[UPSTREAM]** resume file from `outputs/intake/resume_original.pdf` (F1)
- **Processing:** hash + version tag + store in `data/raw/` or `artifacts/raw/`  
- **Outputs (Artifacts):**
  - `artifacts/raw/resume_v1.pdf`
  - `outputs/intake/resume_hash.json`
- **Downstream consumer:**
  - **F5 Resume Parser** (L3)
  - **F16 Audit Log** (L7)
- **Success metrics:** correct version retrieval

---

## L3 — Parsing + Evidence Graph Layer

### F5. Resume Parser → Profile JSON (Value: 5/5)
- **Layer / Stage:** L3  
- **Problem:** Resume text can’t be used reliably until structured.  
- **Inputs:**
  - **[UPSTREAM]** `artifacts/raw/resume_v1.pdf` (F4)
  - **[UPSTREAM]** `outputs/intake/intake_bundle.json` (F1) for target roles/skills emphasis
- **Processing:** extract sections → normalize into schema  
- **Outputs (Artifacts):**
  - `outputs/profile/profile.json`
- **Downstream consumer:**
  - **F6 Evidence Graph Builder** (L3)
  - **F10 Hybrid Ranker** (L5) can use structured skills directly
- **Success metrics:** completeness (skills/experience/education extracted)

### F6. Evidence Graph Builder (Value: 5/5)
- **Layer / Stage:** L3  
- **Problem:** “No evidence, no claim” requires traceable proof nodes.  
- **Inputs:**
  - **[UPSTREAM]** `outputs/profile/profile.json` (F5)
  - **[USER]** project snippets/links (from intake_bundle optional)
- **Processing:** map claims → evidence nodes (project, metrics, dates)  
- **Outputs (Artifacts):**
  - `outputs/evidence/evidence_graph.json`
  - `outputs/evidence/evidence_coverage.json`
- **Downstream consumer:**
  - **F10 Hybrid Ranker** (L5)
  - **F11 Resume Bullets Generator** (L6)
  - **F12 Cover Letter Generator** (L6)
  - **F14 Claim Validator** (L7)
- **Success metrics:** evidence coverage %, unsupported claim list size

---

## L4 — Knowledge + Retrieval (RAG) Layer

### F7. Job Requirements Extractor (Value: 5/5)
- **Layer / Stage:** L4  
- **Problem:** Need structured must-have/nice-to-have signals.  
- **Inputs:**
  - **[UPSTREAM]** `outputs/jobs/job_{id}_raw.txt` (F3)
- **Processing:** schema extraction: skills, tools, seniority, responsibilities  
- **Outputs (Artifacts):**
  - `outputs/jobs/job_{id}_requirements.json`
- **Downstream consumer:**
  - **F9 Constraint Gate** (L5)
  - **F10 Hybrid Ranker** (L5)
  - **F11/F12 Generators** (L6)
- **Success metrics:** human agreement rate on extracted must-haves

### F8. Retrieval of Templates / Career Knowledge Pack (Value: 3/5)
- **Layer / Stage:** L4  
- **Inputs:**
  - **[SYSTEM]** curated templates (cover letter styles, STAR templates)
  - **[UPSTREAM]** job requirements (F7) to query templates
- **Outputs (Artifacts):**
  - `outputs/rag/retrieved_snippets_job_{id}.json`
- **Downstream consumer:**
  - **F11/F12** (L6)
- **Notes:** optional for MVP; helps quality.

---

## L5 — Matching + Ranking Layer

### F9. Constraint Gate (Hard Filters) (Value: 5/5)
- **Layer / Stage:** L5  
- **Problem:** Avoid wasting effort on impossible roles.  
- **Inputs:**
  - **[UPSTREAM]** `outputs/intake/intake_bundle.json` (F1 constraints)
  - **[UPSTREAM]** `outputs/jobs/job_{id}_requirements.json` (F7)
- **Processing:** deterministic checks (remote, location, visa notes, salary band)  
- **Outputs (Artifacts):**
  - `outputs/match/eligibility_report.json`
- **Downstream consumer:**
  - **F10 Hybrid Ranker** (only ranks eligible jobs)
- **Success metrics:** % irrelevant jobs removed; clarity of rejection reasons

### F10. Hybrid Ranker v1 (Value: 5/5)
- **Layer / Stage:** L5  
- **Problem:** Need high-quality shortlist that’s explainable.  
- **Inputs:**
  - **[UPSTREAM]** `outputs/evidence/evidence_graph.json` (F6)
  - **[UPSTREAM]** `outputs/jobs/job_{id}_requirements.json` (F7)
  - **[UPSTREAM]** `outputs/match/eligibility_report.json` (F9)
- **Processing:** weighted score + semantic similarity; output breakdown  
- **Outputs (Artifacts):**
  - `outputs/match/ranked_jobs.json`
- **Downstream consumer:**
  - **F11/F12 Generators** (generate for top job(s))
  - **F2 Explain-My-Rank UI** (L1)
  - **F16 Audit Log** (L7)
- **Success metrics:** top-3 acceptance, ranking consistency

---

## L6 — Generation (LLM) Layer

### F11. Evidence-backed Resume Bullets Generator (Value: 5/5)
- **Layer / Stage:** L6  
- **Problem:** Users need tailored bullets fast, grounded in proof.  
- **Inputs:**
  - **[UPSTREAM]** `outputs/evidence/evidence_graph.json` (F6)
  - **[UPSTREAM]** `outputs/jobs/job_{id}_requirements.json` (F7)
  - **[UPSTREAM]** top job selection from `outputs/match/ranked_jobs.json` (F10)
  - **[UPSTREAM]** optional retrieved snippets (F8)
- **Processing:** generate bullets with evidence ids embedded  
- **Outputs (Artifacts):**
  - `outputs/gen/resume_bullets_job_{id}.md`
  - `outputs/gen/resume_bullets_job_{id}.json`
- **Downstream consumer:**
  - **F14 Claim Validator** (L7)
  - **F17 Package Builder** (L8)
- **Success metrics:** unsupported claim rate ~0; edit distance reduced

### F12. Grounded Cover Letter Generator (Value: 4/5)
- **Layer / Stage:** L6  
- **Inputs:**
  - **[UPSTREAM]** evidence graph (F6)
  - **[UPSTREAM]** job requirements (F7)
  - **[UPSTREAM]** ranked job selection (F10)
  - **[UPSTREAM]** templates (F8 optional)
- **Outputs (Artifacts):**
  - `outputs/gen/cover_letter_job_{id}.md`
- **Downstream consumer:**
  - **F14 Claim Validator** (L7)
  - **F17 Package Builder** (L8)

---

## L7 — Guardrails + Governance Layer

### F14. Claim Validator (“No evidence, no claim”) (Value: 5/5)
- **Layer / Stage:** L7  
- **Problem:** Prevent false claims (the #1 risk in GenAI career tools).  
- **Inputs:**
  - **[UPSTREAM]** generated bullets/letter (F11/F12)
  - **[UPSTREAM]** `outputs/evidence/evidence_graph.json` (F6)
- **Processing:** detect unsupported assertions → block or request evidence  
- **Outputs (Artifacts):**
  - `outputs/guard/validated_resume_bullets_job_{id}.md`
  - `outputs/guard/validated_cover_letter_job_{id}.md`
  - `outputs/guard/blocked_claims_job_{id}.json`
- **Downstream consumer:**
  - **F15 Human Approval** (L7)
  - **F17 Package Builder** (L8)
  - **F16 Audit Log** (L7)
- **Success metrics:** unsupported claim leakage rate (target near zero)

### F15. Human Approval Gate (Value: 5/5)
- **Layer / Stage:** L7  
- **Inputs:**
  - **[UPSTREAM]** validated artifacts (F14)
- **Outputs (Artifacts):**
  - `outputs/guard/approval_job_{id}.json`
- **Downstream consumer:**
  - **F17 Package Builder** (L8)
- **Metric:** prevents accidental export of unapproved content

### F16. Audit Log (Value: 4/5)
- **Layer / Stage:** L7  
- **Inputs:**
  - **[UPSTREAM]** ranked_jobs.json (F10)
  - **[UPSTREAM]** eligibility_report.json (F9)
  - **[UPSTREAM]** blocked_claims.json (F14)
  - **[SYSTEM]** run id, timestamps
- **Outputs (Artifacts):**
  - `outputs/audit/audit_job_{id}.json`
- **Downstream consumer:**
  - UI explanation (F2)
  - Evaluation (L9)

---

## L8 — Workflow + Packaging Layer

### F17. Application Package Builder (Value: 5/5)
- **Layer / Stage:** L8  
- **Inputs:**
  - **[UPSTREAM]** approval_job_{id}.json (F15)
  - **[UPSTREAM]** validated artifacts (F14)
  - **[UPSTREAM]** audit_job_{id}.json (F16)
- **Processing:** create job folder + export files + naming conventions  
- **Outputs (Artifacts):**
  - `exports/{company}_{role}_{date}/resume_v1.md`
  - `exports/{company}_{role}_{date}/cover_letter_v1.md`
  - `exports/{company}_{role}_{date}/audit.json`
- **Downstream consumer:** user (final deliverable)  
- **Success metrics:** export success, consistent structure

---

## L9 — Platform Ops Layer
### F19. MLflow Tracking (Value: 3/5)
- **Inputs:** [SYSTEM] run config, scores, prompt versions  
- **Outputs:** MLflow runs for reproducibility  
- **Downstream:** evaluation/iteration

### F20. DVC Versioning (Value: 3/5)
- **Outputs:** versioned datasets/artifacts  
- **Downstream:** reproducible pipelines

### F21. CI/CD Skeleton (Value: 2/5)
- **Outputs:** automated tests + build

### F22. Observability + Monitoring (Value: 2/5)
- **Outputs:** structured logs/metrics  
- **Downstream:** debugging + uptime

### F23. Evidently Drift/Eval (Value: 2/5)
- **Outputs:** drift reports on ranking features  
- **Downstream:** model quality control

### F24. Kafka Streaming (Value: 1/5)
- **Outputs:** event stream for scaling  
- **Downstream:** async workflows

---

# 3) End-to-end flow summary (pipeline)
1) **F1 Intake** → `intake_bundle.json`  
2) **F4 Store resume** → `resume_v1.pdf`  
3) **F5 Parse** → `profile.json`  
4) **F6 Evidence Graph** → `evidence_graph.json`  
5) **F3 Job ingest** → `job_raw.txt`  
6) **F7 Extract requirements** → `job_requirements.json`  
7) **F9 Constraint gate** → `eligibility_report.json`  
8) **F10 Rank** → `ranked_jobs.json`  
9) **F11/F12 Generate** → `resume_bullets.md`, `cover_letter.md`  
10) **F14 Validate** → `validated_*` + `blocked_claims.json`  
11) **F15 Approve** → `approval.json`  
12) **F17 Export** → `/exports/.../` + `audit.json`

---

# 4) What to check before finalizing this file
- Every feature must produce at least one artifact.
- Every artifact must have a consumer downstream (or be final output).
- Every feature should map to exactly one primary layer.
