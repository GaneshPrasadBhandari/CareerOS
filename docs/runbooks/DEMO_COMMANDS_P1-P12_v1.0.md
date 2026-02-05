runbooks/DEMO_COMMANDS_P1-P12_v1.0.md

# CareerOS Demo Commands Runbook (P1 → P12) v1.0

This runbook is designed for live demos. Copy/paste commands directly into Terminal.

It includes:
- environment setup
- running API + UI
- verifying artifacts for every stage
- PASS + BLOCK governance proof

---

## 0) Go to repo root + activate venv

```bash
cd /Users/ganeshprasadbhandari/Documents/D_drive/clark/spring_2026/capstone/CareerOS
source .venv/bin/activate

---

## 1) Install dependencies (only if missing)
```bash
python -m pip install -U pip
python -m pip install pytest pandas python-docx reportlab

---

## 2) Run tests (demo proof: engineering quality)
```bash
PYTHONPATH=src pytest -q

---

## 3) Start API (Terminal 1)
```bash
PYTHONPATH=src uvicorn apps.api.main:app --reload --port 8000

---
Keep this running.


##4) Start UI (Terminal 2)
```bash
CAREEROS_API_URL=http://127.0.0.1:8000 streamlit run apps/ui/Home.py

---

Use Streamlit to paste resume/job and click buttons for P1–P12.

## PASS Demo Checklist (P1 → P12)
### P1 — Verify Intake bundle artifacts

### After clicking P1 in Streamlit:
```bash
ls -lt outputs/intake | head

---

### P2 — Verify EvidenceProfile artifacts

After clicking P2 (parse resume):
```bash
ls -lt outputs/profile | head

---

### P3 — Verify JobPost artifacts

After clicking P3 (ingest jobs):
```bash
ls -lt outputs/jobs | head

---

### P4 — Verify MatchResult artifacts

After clicking P4 (matching):
```bash
ls -lt outputs/matching | head

---

### P5 — Verify RankedShortlist artifacts

After clicking P5 (ranking):
```bash
ls -lt outputs/ranking | head

---

### P6 — Verify ApplicationPackage artifacts

After clicking P6 (generation):
```bash
ls -lt exports/packages | head

---

### P7 — Verify Guardrails report (PASS)

After clicking P7 validate:
```bash
ls -lt outputs/guardrails | head

---

###Print latest report status quickly:
```bash
PYTHONPATH=src python - <<'PY'
import glob, json
p = sorted(glob.glob("outputs/guardrails/validation_report_v1_*.json"))[-1]
d = json.load(open(p))
print("LATEST:", p)
print("status:", d.get("status"))
print("unsupported_terms:", d["findings"][0].get("unsupported_terms") if d.get("findings") else [])
PY

---
Expected: status: pass


### P8 — Verify exports + tracking ledger

After clicking P8 export:
```bash
ls -lt exports/submissions | head
find exports/submissions -maxdepth 3 -type f | tail -n 20
tail -n 3 outputs/apply_tracking/applications_v1.jsonl

---

### P9 — Verify analytics source (ledger exists)

P9 is UI/API derived, but the ledger is the source of truth:
```bash
tail -n 5 outputs/apply_tracking/applications_v1.jsonl

---

### P10 — Verify followups queue

After clicking P10 generate actions:
```bash
ls -lt outputs/followups | head
cat outputs/followups/followups_v1.json | head -n 120

---

### P11 — Verify drafts bundle

After clicking P11 build drafts:
```bash
ls -lt outputs/notifications | head
cat outputs/notifications/drafts_v1.json | head -n 120

---

### P12 — Orchestrator run (optional PASS)

After clicking P12 run (or calling the API), verify downstream artifacts exist:
```bash
ls -lt exports/packages | head
ls -lt outputs/guardrails | head
ls -lt exports/submissions | head
ls -lt outputs/followups | head
ls -lt outputs/notifications | head
---

## BLOCK Demo (Governance proof)

Goal: show that an unsupported claim is blocked, and export stops.

Run this local guardrail proof (Snowflake is not in evidence skills):
```bash
PYTHONPATH=src python - <<'PY'
from careeros.parsing.schema import EvidenceProfile
from careeros.generation.schema import ApplicationPackage, ResumeBullet, CoverLetterDraft
from careeros.guardrails.service import validate_package_against_evidence

profile = EvidenceProfile(raw_text="x", skills=["python","docker"], titles=[], domains=[])
pkg = ApplicationPackage(
    run_id="demo_block",
    profile_path="p.json",
    job_path="j.json",
    bullets=[ResumeBullet(text="Built pipelines using Python, Docker, Snowflake")],
    evidence_skills=["python","docker"],
    cover_letter=CoverLetterDraft(subject="s", paragraphs=["Hello"]),
    qa_stubs={"Why fit?":"x"},
)
rep = validate_package_against_evidence(profile, pkg, run_id="demo_block", package_path="pkg.json")
print("status:", rep.status)
print("unsupported_terms:", rep.findings[0].unsupported_terms if rep.findings else [])
PY

---
Expected:

status: blocked

unsupported_terms: ['snowflake']

## Optional: confirm export folder does NOT grow after a blocked attempt:
```bash
ls -lt exports/submissions | head

---

## Logs (show auditability)
```bash
tail -n 50 logs/careeros.jsonl

---

Also show API terminal logs (uvicorn requests) during the demo.

## Quick reset for a fresh demo (optional)

If you want to start with clean runtime artifacts (do NOT commit these):
```bash
rm -rf outputs/intake outputs/profile outputs/jobs outputs/matching outputs/ranking outputs/guardrails outputs/followups outputs/notifications outputs/apply_tracking
rm -rf exports/submissions exports/packages
mkdir -p outputs/intake outputs/profile outputs/jobs outputs/matching outputs/ranking outputs/guardrails outputs/followups outputs/notifications outputs/apply_tracking
mkdir -p exports/packages exports/submissions

---

Then rerun the PASS demo.