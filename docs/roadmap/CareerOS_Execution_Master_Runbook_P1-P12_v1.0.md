# CareerOS Capstone — Execution Master Runbook (P1 → P12) v1.0

This document is the single source of truth for running and demoing CareerOS end-to-end.
Use it to continue work in a new chat without restarting.

---

## 1) System Goal

CareerOS is an evidence-grounded, agentic career workflow that takes:
- candidate intake + resume evidence
- multiple job posts

…and produces:
- explainable matching + ranking
- job-specific application packages
- guardrails that block unsupported claims
- exports (DOCX/PDF)
- apply tracking ledger + funnel analytics
- follow-up action queue + communication drafts
- one-click orchestration runner (agent-ready spine)

Phase 0 = deterministic pipeline first (P1–P12), then agentic layers (Arch L2/L3/L4) + MLflow/DVC.

---

## 2) No-Confusion Mapping Rule

- P# = pipeline stages (implementation build order)
- Arch L# = macro architecture responsibility layers (your diagram)
- One pipeline stage may belong to multiple Arch layers.

---

## 3) Repo & Runtime State (Verified Working)

✅ Python venv working  
✅ FastAPI backend runs via Uvicorn  
✅ Streamlit UI runs and calls backend  
✅ Artifacts persist to disk under `outputs/` and `exports/`  
✅ `outputs/` is gitignored (correct)  
✅ `pytest` configured and used  
✅ Guardrails fixed to avoid false positives  
✅ Export deps installed: `python-docx`, `reportlab`  
✅ Dashboard deps installed: `pandas`  
✅ UI supports env-based API URL: `CAREEROS_API_URL`

Logs:
- Structured logs: `logs/careeros.jsonl` (tail for demo evidence)

---

## 4) Pipeline Stages Summary (P1 → P12)

### P1 — Intake Bundle (User preferences → IntakeBundle)
**Purpose:** Capture targeting constraints (roles/location/salary/work auth/remote) into a stable contract.  
**Arch:** L1 Entry Layer (UI/API).  
**Output:** `outputs/intake/intake_bundle_v1_<timestamp>.json`

---

### P2 — Resume Parsing (Resume text → EvidenceProfile)
**Purpose:** Convert resume into evidence model (truth source for allowed claims).  
**Arch:** L4 Agent behavior + supports L9 governance.  
**Output:** `outputs/profile/profile_v1_<timestamp>.json`

---

### P3 — Job Ingestion (Job text → JobPost)
**Purpose:** Normalize job descriptions into structured job objects.  
**Arch:** L4 Agent behavior.  
**Output:** `outputs/jobs/job_post_v1_<timestamp>.json`

---

### P4 — Matching (EvidenceProfile + JobPost → MatchResult)
**Purpose:** Explainable overlap/missing + score (0–100).  
**Arch:** L3 Manager + L4 Agent.  
**Output:** `outputs/matching/match_result_v1_<timestamp>.json`

---

### P5 — Ranking (All jobs → RankedShortlist)
**Purpose:** Sort multiple jobs into Top-N with reasons.  
**Arch:** L3 Manager (Job Ops).  
**Output:** `outputs/ranking/shortlist_v1_<timestamp>.json`

---

### P6 — Generation (Shortlist + Evidence → ApplicationPackage)
**Purpose:** Generate job-specific package (bullets + cover letter + QA stubs), grounded in overlap skills.  
**Arch:** L4 Agent behavior; later L8 Models/Memory.  
**Output:** `exports/packages/application_package_v1_<jobhint>_<timestamp>.json`

---

### P7 — Guardrails (Package → ValidationReport pass/blocked)
**Purpose:** Prove governance: block unsupported claims (MVP requirement).  
**Arch:** L9 Governance/Ops + L5 Human Gates.  
**Rule GR001 (Phase 0 final):** Block only if known tool/tech terms appear that are not in `EvidenceProfile.skills`. Avoid false positives.  
**Output:** `outputs/guardrails/validation_report_v1_<timestamp>.json`

---

### P8 — Export + Apply Tracking (Validated Package → DOCX/PDF + Ledger)
**Purpose:** Export submit-ready artifacts and track application lifecycle.  
**Arch:** L6 Execution Ops + L9 Governance.  
**Outputs:**
- `exports/submissions/<application_id>_<job_hint>/application_package.docx`
- `exports/submissions/<application_id>_<job_hint>/application_package.pdf`
- `outputs/apply_tracking/applications_v1.jsonl`

---

### P9 — Analytics Dashboard (Ledger → Funnel + List + Drill-Down)
**Purpose:** Observability of pipeline outcomes and conversion funnel.  
**Arch:** L7 Observability + supports L6/L9.  
**API:**
- `GET /applications/metrics`
- `GET /applications/list?status=&limit=`
- `GET /applications/{application_id}`

---

### P10 — Next Actions (Ledger → Follow-up Action Queue)
**Purpose:** Deterministic “what to do next” queue (follow-ups, interview prep, stale closure).  
**Arch:** L6 + L7 + L9.  
**Output:** `outputs/followups/followups_v1.json`

---

### P11 — Notification Drafts (Action Queue → Email/LinkedIn Drafts)
**Purpose:** Ready-to-copy communication drafts (Phase 0 = no sending).  
**Arch:** L6 + L7 + L9; later L5 approval.  
**Output:** `outputs/notifications/drafts_v1.json`

---

### P12 — Orchestration Runner (One-click: P6→P7→P8→P10→P11)
**Purpose:** Agent-ready workflow spine with strict gating.  
**Arch:** L3 Manager + L6 + L9 (interfaces with L4 later).  
**Behavior:** If P7 blocks → stop, no exports/actions/drafts. If pass → complete downstream steps.

---

## 5) How to Run (API + UI + Tests)

### Install dependencies (if needed)
```bash
source .venv/bin/activate
python -m pip install -U pip
python -m pip install pytest pandas python-docx reportlab

#Run tests
PYTHONPATH=src pytest -q

#Run API
PYTHONPATH=src uvicorn apps.api.main:app --reload --port 8000

#Run UI
CAREEROS_API_URL=http://127.0.0.1:8000 streamlit run apps/ui/Home.py

---

6) Demo Proof Sequence (P1 → P12)
A) PASS Demo (happy path)

P1 Create Intake Bundle → confirm file path

P2 Parse Resume → confirm profile artifact

P3 Ingest 2–3 Job Posts → confirm job artifacts

P4 Run Matching → confirm match_result

P5 Run Ranking → confirm shortlist

P6 Generate Package → confirm package JSON

P7 Validate → status = pass

P8 Export → DOCX/PDF created + tracking record written

P9 Analytics → funnel + list + drill-down by application_id

P10 Generate Next Actions → actions appear

P11 Build Drafts → drafts appear + open by draft_id

(Optional) P12 Orchestrator → run summary shows all steps ok

B) BLOCK Demo (governance proof)

Generate package (P6)

Inject an unsupported tool term (e.g., Snowflake) not in EvidenceProfile.skills

P7 Validate → status = blocked + unsupported_terms includes snowflake

Confirm P8 export does not run / no new submission folder

Confirm P12 stops at guardrails if using orchestrator

7) Where Outputs Are Saved (Quick Reference)

P1: outputs/intake/

P2: outputs/profile/

P3: outputs/jobs/

P4: outputs/matching/

P5: outputs/ranking/

P6: exports/packages/

P7: outputs/guardrails/

P8: exports/submissions/ and outputs/apply_tracking/

P9: UI + API responses; source ledger is outputs/apply_tracking/applications_v1.jsonl

P10: outputs/followups/

P11: outputs/notifications/

P12: API/UI response JSON + artifacts created by underlying stages

---

## 8) How to Inspect Outputs (CLI)
```bash
ls -lt outputs/intake | head
ls -lt outputs/profile | head
ls -lt outputs/jobs | head
ls -lt outputs/matching | head
ls -lt outputs/ranking | head
ls -lt exports/packages | head
ls -lt outputs/guardrails | head
ls -lt exports/submissions | head
tail -n 3 outputs/apply_tracking/applications_v1.jsonl
cat outputs/followups/followups_v1.json | head -n 80
cat outputs/notifications/drafts_v1.json | head -n 80

---

## Logs:
```bash
tail -n 30 logs/careeros.jsonl
---

## 9) Current Checkpoint

✅ Phase 0 pipeline completed through P12, stable and demo-ready.
Next: Begin Agentic Architecture layers (Arch L2 → L3 → L4), then integrate MLflow + DVC once agent wiring is stable.


