# CareerOS — PROJECT_HANDOFF_MASTER (Continuity Anchor) v1.0
**Project:** CareerOS Agentic AI Capstone  
**Owner:** Ganesh Prasad Bhandari  
**Timezone:** America/New_York  
**Last Updated:** 2026-02-06  
**Current Focus:** **Phase 2 (Agentic Core) — Starting P13 → P15**

---

## 1) BLUF (What this project is + why it matters)
CareerOS is an evidence-grounded, agentic career workflow that turns:
- **resume + candidate constraints**
- **multiple job descriptions**
into:
- a **ranked shortlist**
- a **job-specific application package (resume bullets + cover letter + Q/A stubs)**
- **guardrails that block unsupported claims**
- exportable submission documents (DOCX/PDF)
- application tracking + follow-up actions + outreach drafts
- a one-click orchestrator run that chains these steps with full audit trace

**Core promise:** CareerOS does not invent skills. Anything not supported by the EvidenceProfile gets blocked by P7 guardrails.

---

## 2) Architecture mapping rule (no confusion)
- **P#** = pipeline build stages (implementation order)
- **Arch L#** = architecture responsibility layers (macro design)

A single P-stage can belong to multiple Arch layers.

**High-level mapping**
- **P1–P3**: Arch L1 Entry + Arch L4 Understanding
- **P4–P5**: Arch L3 Managers (matching/ranking)
- **P6**: Arch L4 Agents (generation behavior), later Arch L8 (LLM/RAG)
- **P7**: Arch L9 Governance + touches Arch L5 Approval gates
- **P8–P11**: Arch L7 Analytics + Arch L5 Ops workflows
- **P12**: Arch L2 Orchestrator (Phase-0 deterministic orchestration)

---

## 3) Repo baseline (what is stable today)
✅ Python venv works  
✅ FastAPI backend runs (Uvicorn)  
✅ Streamlit UI runs and calls API  
✅ Artifacts are written under `outputs/` and `exports/`  
✅ Logs are written under `logs/careeros.jsonl`  
✅ `pytest` runs unit + integration tests (Phase-1 stable)  
✅ `outputs/` and `exports/` are not committed (gitignored)  
✅ P12 orchestration runs P6→P11 end-to-end

---

## 4) Phase 1 completed (P1 → P12) — What each stage does

### P1 — Intake Bundle
**Input:** candidate constraints (role, location, salary, remote, work auth)  
**Output:** `outputs/intake/intake_bundle_v1_*.json`

### P2 — Resume Parsing → EvidenceProfile
**Input:** resume text  
**Output:** `outputs/profile/profile_v1_*.json`  
**Purpose:** proof-grounded skills/titles/domains (truth source)

### P3 — Job Ingestion → JobPost
**Input:** job description text (optional URL)  
**Output:** `outputs/jobs/job_post_v1_*.json`

### P4 — Matching → MatchResult
**Input:** EvidenceProfile + JobPost  
**Output:** `outputs/matching/match_result_v1_*.json`  
**Purpose:** overlap skills, missing skills, explainable score

### P5 — Ranking → RankedShortlist
**Input:** EvidenceProfile + all JobPosts  
**Output:** `outputs/ranking/shortlist_v1_*.json`  
**Purpose:** Top-N prioritized jobs

### P6 — Generation → ApplicationPackage
**Input:** EvidenceProfile + top job + overlap skills  
**Output:** `exports/packages/application_package_v1_*.json`  
**Purpose:** resume bullets + cover letter + Q/A stubs (Phase-0 deterministic)

### P7 — Guardrails → ValidationReport (PASS/BLOCK)
**Input:** EvidenceProfile + ApplicationPackage  
**Output:** `outputs/guardrails/validation_report_v1_*.json`  
**Purpose:** block unsupported claims (GR001 skills rule)

### P8 — Export + Tracking
**Input:** latest validated pass package  
**Output:**  
- `exports/submissions/<application_id>.../application_package.docx`  
- `exports/submissions/<application_id>.../application_package.pdf`  
- `outputs/apply_tracking/applications_v1.jsonl` (ledger)

### P9 — Analytics
**Input:** tracking ledger (`applications_v1.jsonl`)  
**Output:** API/UI provides list + funnel metrics (source is ledger)

### P10 — Followups (Next Actions Queue)
**Input:** tracking ledger + followup_days + stale_days  
**Output:** `outputs/followups/followups_v1.json`

### P11 — Notifications (Drafts from Actions)
**Input:** followups queue  
**Output:** `outputs/notifications/drafts_v1.json`

### P12 — One-Click Orchestration (P6→P11)
**Input:** profile_path + job_path + overlap_skills + followup config  
**Output:** `outputs/orchestrator/orchestrator_run_v1_*.json` + all downstream artifacts  
**Final status:** ok/blocked/error with step trace

---

## 5) Output locations (where everything is saved)
**Artifacts**
- `outputs/intake/` (P1)
- `outputs/profile/` (P2)
- `outputs/jobs/` (P3)
- `outputs/matching/` (P4)
- `outputs/ranking/` (P5)
- `exports/packages/` (P6)
- `outputs/guardrails/` (P7)
- `exports/submissions/` (P8 export)
- `outputs/apply_tracking/applications_v1.jsonl` (P8 ledger)
- `outputs/followups/` (P10)
- `outputs/notifications/` (P11)
- `outputs/orchestrator/` (P12)

**Logs**
- `logs/careeros.jsonl` (structured event logs)

---

## 6) How to run (Phase 1 + Phase 2 baseline)

### 6.1 Activate environment
```bash
cd /path/to/CareerOS
source .venv/bin/activate
```
---

## 6.2 Install deps (only if missing)
```bash
python -m pip install -U pip
python -m pip install pytest pandas 
python-docx reportlab
```

## 6.3 Run tests
```bash
PYTHONPATH=src pytest -q
```

## 6.4 Run API (Terminal 1)
```bash
PYTHONPATH=src uvicorn apps.api.main:app --reload --port 8000
```

## 6.5 Run UI (Terminal 2)
```bash
CAREEROS_API_URL=http://127.0.0.1:8000 streamlit run apps/ui/Home.py
```
---

7) Demo proof sequence (P1 → P12)
UI Flow

P1 create intake

P2 parse resume

P3 ingest 1–3 job posts

P5 rank (optional P4 per job)

P6 generate package

P7 validate (PASS)

P8 export + tracking

P9 list + analytics

P10 followups queue

P11 drafts bundle

P12 run orchestrator end-to-end

Governance BLOCK proof

Add an unsupported skill in a generated bullet (e.g., “Snowflake” not in EvidenceProfile.skills)

Run validate (P7) → status becomes blocked

Show ValidationReport findings

8) Known issues solved (keep this list updated)
pytest missing: ensure .venv activated and install pytest

from __future__ import annotations must be top of file

Missing modules: install python-docx and reportlab for export

Guardrails false positives: updated to ignore common words + use allow/deny logic

Followups service API mismatch: aligned schema fields and functions

Orchestrator PosixPath serialization: ensure outputs are JSON safe (strings)

Streamlit DuplicateElementId: add unique key= to duplicate widgets

Tracking update 404: ensure application_id exists in ledger

9) Current status right now (handoff checkpoint)
✅ Phase 1 (P1–P12) is working end-to-end
✅ P12 returns final_status ok and generates exports + followups + drafts
✅ Integration health test uses apps.api.main (not mainold)

Next: Start Phase 2 (Agentic Core): P13 → P15

10) Phase 2 plan (what we’re building next)
Phase 2A — Agentic Core (NO LLM yet)
P13 State model + Tool Registry
P14 Deterministic agentic orchestrator (manager planning + tool calling)
P15 Human approval gate enforced (export/apply requires approval artifact)

Phase 2B — Hardening + Intelligence
P16 Run trace + replay system
P17 Regression harness + evaluation metrics
P18 LLM + RAG integration (still guardrails + approval)

11) New chat bootstrap message (copy/paste into any new chat)
CareerOS continuation.

Current status:
- Phase 1 complete (P1–P12). P12 orchestrator runs P6→P11 end-to-end.
- Starting Phase 2 now: P13 (State model + Tool registry), then P14 (deterministic agentic orchestrator), then P15 (human approval gate).

Repo anchors:
- roadmap/PROJECT_HANDOFF_MASTER.md
- roadmap/CAREEROS_PHASE2_STRATEGY_v1.0.md
- runbooks/DEMO_COMMANDS_P1-P12_v1.0.md

Current task:
<one sentence>

If debugging:
Failing command + error:
<paste>
Files changed:
<list>
12) Git hygiene (non-negotiable)
.env must never be committed

outputs/ and exports/ remain gitignored

Commit:

code

tests

runbooks

roadmap docs

schemas/services

13) Immediate next action (Phase 2 kickoff)
Start P13:

src/careeros/state/schema.py (CareerOSState + StepEvent)

src/careeros/tools/registry.py (wrap P1–P12 services as tools)

src/careeros/state/store.py (save/load/latest)

Tests for state roundtrip + tool smoke

Add API endpoint /agentic/run in P14 (after P13 complete)