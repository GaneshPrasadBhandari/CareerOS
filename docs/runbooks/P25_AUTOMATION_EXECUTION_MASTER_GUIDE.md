# CareerOS P25 Automation — Execution Master Guide (Single Source of Truth)

This is the consolidated runbook for the current automation step.
It explains inputs, outputs, storage paths, layer handoffs, agent roles, execution commands, and open-source stack choices.

## 1) Goal of this step

Deliver one-click and API-driven P25 automation with auditable artifacts:

- Resume parse (`txt/pdf/docx`)
- Job ingestion (manual text + URL connector)
- Match -> rank -> package -> guardrails
- Optional local LLM summary (Ollama)
- Execution trace showing layer-to-layer data transmission

## 2) Open-source stack policy (free-first)

- Orchestration: FastAPI + deterministic workflow + LangGraph-compatible flow
- LLM: Ollama local models (no paid OpenAI required)
- Parsing: `pypdf`, `python-docx`, plain text parser
- Connector: `httpx` fetch + HTML-to-text extraction
- Storage: JSON artifacts under `outputs/` and `exports/`
- Optional vector/memory evolution: Chroma/Qdrant in subsequent step

## 3) P25 APIs in this step

- `POST /p25/automation/run`
  - JSON payload flow (inline text and optional connector URLs)
- `POST /p25/automation/run_upload`
  - Multipart upload flow (resume file + job file)
- `GET /p25/automation/trace/latest`
  - Retrieve latest execution trace (optional `run_id` filter)
- `GET /p25/system/health`
  - Runtime readiness checks

## 4) Inputs and how to run

### A) Upload-based one-click run (recommended)

```bash
curl -s -X POST http://127.0.0.1:8000/p25/automation/run_upload \
  -F candidate_name="Riya Patel" \
  -F top_n=3 \
  -F resume_file=@data/demo/resume_sample_backend_ml.txt \
  -F job_file=@data/demo/job_description_ml_platform.txt | jq
```

### B) JSON-based automation run

```bash
curl -s -X POST http://127.0.0.1:8000/p25/automation/run \
  -H 'Content-Type: application/json' \
  -d "$(python - <<'PYJSON'
import json
from pathlib import Path
resume = Path('data/demo/resume_sample_backend_ml.txt').read_text(encoding='utf-8')
job = Path('data/demo/job_description_ml_platform.txt').read_text(encoding='utf-8')
print(json.dumps({
  'run_id': 'demo_p25_master',
  'candidate_name': 'Riya Patel',
  'top_n': 3,
  'resume': {'source_type': 'inline', 'text': resume},
  'jobs': {'job_texts': [job], 'urls': []}
}))
PYJSON
)" | jq
```

### C) Check trace artifact

```bash
curl -s "http://127.0.0.1:8000/p25/automation/trace/latest" | jq
```

## 5) Layer-by-layer execution mapping (L2->L8)

### L2 Parsing
- Agent: `parser`
- Input: resume file/text
- Output: profile artifact + extracted skills
- Storage: `outputs/profile/`
- Next input target: L3 jobs

### L3 Jobs
- Agent: `connector` (or direct job text parser)
- Input: job text list and/or job URLs
- Output: job artifacts
- Storage: `outputs/jobs/` and connector logs in `outputs/phase3/connectors/`
- Next input target: L4 matching

### L4 Matching
- Agent: `matcher`
- Input: profile + selected job
- Output: match artifact + score
- Storage: `outputs/matching/`
- Next input target: L5 ranking

### L5 Ranking
- Agent: `ranker`
- Input: profile + job candidates
- Output: shortlist artifact
- Storage: `outputs/ranking/`
- Next input target: L6 generation

### L6 Generation
- Agent: `generator`
- Input: top-ranked job + profile
- Output: package (bullets + cover letter + QA)
- Storage: `exports/packages/`
- Next input target: L7 guardrails

### L7 Guardrails
- Agent: `guardrails`
- Input: package + evidence profile
- Output: validation report (`pass`/`blocked`)
- Storage: `outputs/guardrails/`
- Next input target: L8 summary

### L8 Summary
- Agent: `llm_summary`
- Input: run metadata + match score
- Output: summary text (Ollama) or degraded fallback
- Storage: included in API response + trace artifact
- Next input target: complete

## 6) Output artifact paths for this step

- `outputs/profile/*.json`
- `outputs/jobs/*.json`
- `outputs/matching/*.json`
- `outputs/ranking/*.json`
- `exports/packages/*.json`
- `outputs/guardrails/*.json`
- `outputs/phase3/connectors/*.json`
- `outputs/phase3/parser/*.json`
- `outputs/phase3/p25_runs/*.json` (execution trace)
- `outputs/phase3/p25_system_checks/*.json` (runtime health)

## 7) Agents used now and implementation quality strategy

Agents currently implemented:
- parser
- connector
- matcher
- ranker
- generator
- guardrails
- llm_summary

Quality strategy in this step:
- deterministic, auditable artifacts
- strict handoff between layers with trace map
- no paid-model dependency
- graceful degradation when optional services are absent
- integration tests for both JSON and upload flows

## 8) Streamlit usage for this step

1. `scripts/run_phase2_app.sh api`
2. `scripts/run_phase2_app.sh ui`
3. Open Streamlit and use:
   - **P25 — One-Click Automation (Upload Resume + Job File)**
4. Upload resume + job files and run
5. Inspect returned `paths.trace_path` and other artifacts

## 9) What is next after this step

- Add authenticated connectors for major job sources (compliance-safe)
- Add vector retrieval/reranking in default P25 path
- Add model routing policy for local models (task-specific)
- Add stronger ATS template controls and evaluator score thresholds
