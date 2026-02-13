# Phase3 Demo Inputs, End-to-End Test Path, and Automation Status

This runbook gives you copy/paste demo inputs for Streamlit + API testing and explains what is automated vs manual today.

---

## 1) Quick branch sync (safe baseline)

```bash
git fetch origin --prune
git checkout phase3-dev
git pull --rebase origin phase3-dev
```

If you want a new feature branch from latest `phase3-dev`:

```bash
git checkout -b feat/p25-<short-topic>
```

---

## 2) Start backend + UI

Terminal A (API):

```bash
scripts/run_phase2_app.sh api
```

Terminal B (UI):

```bash
scripts/run_phase2_app.sh ui
```

Open Streamlit and keep API URL as:

```text
http://127.0.0.1:8000
```

---

## 3) Demo inputs you can use immediately

### Resume input (L2)

Use file: `data/demo/resume_sample_backend_ml.txt`

### Job description input (L3)

Use file: `data/demo/job_description_ml_platform.txt`

### Intake values (L1 suggested)

- Candidate name: `Riya Patel`
- Target roles: `ML Platform Engineer, Backend Engineer, GenAI Engineer`
- Preferred location: `USA`
- Remote only: `true`
- Salary min/max: `120000 / 180000`
- Work authorization: `US work authorized`

---

## 4) API smoke using the same demo data

```bash
# Health + phase status
curl -s http://127.0.0.1:8000/health | jq
curl -s http://127.0.0.1:8000/phases/status | jq

# L1 Intake
curl -s -X POST http://127.0.0.1:8000/intake \
  -H 'Content-Type: application/json' \
  -d '{
    "version":"v1",
    "candidate_name":"Riya Patel",
    "target_roles":["ML Platform Engineer","Backend Engineer","GenAI Engineer"],
    "target_industries":["SaaS","AI"],
    "constraints":{"location":"USA","remote_only":true,"salary_min":120000,"salary_max":180000,"work_auth":"US work authorized","relocation_ok":false},
    "links":{"linkedin_url":null,"github_url":null,"portfolio_url":null},
    "notes":"demo run"
  }' | jq
```

Then use Streamlit for L2/L3 paste flow, or post `/profile` and `/jobs/ingest` with file contents.

---

## 5) Where outputs are stored

- Intake bundle: `outputs/intake/`
- Parsed profile: `outputs/profile/`
- Ingested jobs: `outputs/jobs/`
- Match artifacts: `outputs/matching/`
- Ranking shortlist: `outputs/ranking/`
- Generated package: `exports/packages/`
- Guardrails reports: `outputs/guardrails/`
- P22 approvals: `outputs/phase3/p22_approval/`
- P23 memory: `outputs/phase3/p23_memory/`
- P24 evaluations: `outputs/phase3/p24_eval/`
- P25 health snapshots: `outputs/phase3/p25_system_checks/`

---

## 6) P1–P25 and L1–L9: manual vs automated (current state)

### Automated now

- L1 Intake artifact write.
- L2 Resume text parsing (rule/keyword based profile extraction).
- L3 Job text parsing (rule/keyword based keyword extraction).
- L4 Matching score creation.
- L5 Ranking shortlist generation.
- L6 Package generation templates.
- L7 Guardrails validation report.
- L8 Export + tracking APIs.
- L9 dashboard metrics APIs.
- P20 contract validation route.
- P21 graph run route (LangGraph path + deterministic fallback).
- P22/P23/P24/P25 scaffolding routes and file-backed state/eval/health.

### Manual or partial today

- Resume upload parsing from PDF/DOCX in UI (currently paste-text first).
- Auto scraping top job portals end-to-end.
- Production vector DB retrieval + embeddings orchestration in core pipeline.
- Fully model-driven LLM generation for every step.
- Multi-agent live orchestration with external agent platform connectors.

So yes, the app is **partially automated** today: deterministic pipeline automation exists; full autonomous agent + model stack is staged and partly scaffolded.

---

## 7) Free/open-source model plan (no paid OpenAI required)

Recommended default stack for next iterations:

- LLM: Ollama-hosted models (Llama 3.x / Qwen / Mistral families)
- Embeddings: BGE or E5 from Hugging Face
- Vector DB: Chroma or Qdrant (self-hosted)
- OCR: Tesseract + PaddleOCR
- Document parsing: `pypdf`, `python-docx`, `unstructured`
- Orchestration: LangGraph (+ optional CrewAI adapter later)

---

## 8) One-command diagnostics

```bash
scripts/phase3_doctor.sh
python scripts/plot_phase3_flow.py
```

This checks route availability and writes diagrams under `outputs/phase3/`.



## 9) P25 full automation API demo (resume parser + jobs + ranking + package + guardrails + LLM summary)

```bash
curl -s -X POST http://127.0.0.1:8000/p25/automation/run   -H 'Content-Type: application/json'   -d "$(python - <<'PYJSON'
import json
from pathlib import Path
resume = Path('data/demo/resume_sample_backend_ml.txt').read_text(encoding='utf-8')
job = Path('data/demo/job_description_ml_platform.txt').read_text(encoding='utf-8')
payload = {
  'run_id': 'demo_p25_auto',
  'candidate_name': 'Riya Patel',
  'top_n': 3,
  'resume': {'source_type': 'inline', 'text': resume},
  'jobs': {'job_texts': [job]}
}
print(json.dumps(payload))
PYJSON
)" | jq
```

Expected response sections:

- `parser`: resume parsing outcome (skills, section hits, parser artifact path)
- `connector`: job connector summary (urls attempted/errors)
- `paths`: profile/job/match/shortlist/package/validation artifact paths
- `metrics`: `match_score`, `jobs_ingested`, `guardrails_status`
- `llm_summary`: Ollama-based summary (or `degraded` if Ollama is not running)

---

## 10) Streamlit UI test flow (all major steps)

1. Start API: `scripts/run_phase2_app.sh api`
2. Start UI: `scripts/run_phase2_app.sh ui`
3. In UI:
   - set API URL = `http://127.0.0.1:8000`
   - click **Check API Health**
   - L1: fill intake values and click **Create Intake Bundle**
   - L2: paste `data/demo/resume_sample_backend_ml.txt` and click **Build Profile**
   - L3: paste `data/demo/job_description_ml_platform.txt` and click **Ingest Job Post**
   - L4: click **Run Matching**
   - L5: click **Run Ranking**
   - L6: click **Generate Application Package**
   - L7: click **Validate Latest Package**
   - Phase3: call `/p21/langgraph/run`, `/p24/evaluator/run_v2`, `/p25/system/health` from API/terminal

Tip: if UI shows `Connection refused`, your API process is not running on `:8000`.

