# P24 Evaluator v2 + P25 Free-Stack Implementation Plan

This runbook clarifies **what is already done** vs **what is next**.

## 1) Clarification: why "P24 done" and still "P24 v2"?

- **P22/P23/P24 are currently `ready` as API scaffolding** (contracts + basic artifact flow).
- Current P24 evaluator is a **v1 baseline** that computes a simple completeness score.
- **P24 v2** means improving evaluator quality (better KPIs, weighted scoring, trend reports).

So there is no contradiction:
- P24 baseline = done
- P24 advanced evaluator = next improvement before/alongside P25

---

## 2) Current baseline (already implemented)

- `POST /p24/evaluator/run` exists and writes evaluation artifacts.
- Score currently checks existence of shortlist/validation/approval evidence.

Reference file:
- `src/careeros/phase3/next_steps.py`

---

## 3) P24 Evaluator v2 (next concrete implementation)

## 3.1 KPIs and weights

Proposed weighted score (0-100):
- **Match quality** (30): normalized top-1 score from ranking
- **Guardrails quality** (25): pass/blocked + severity deductions
- **Approval quality** (20): approved/rejected + reviewer notes completeness
- **Package quality** (15): bullets count, citation completeness (v2 package if available)
- **Pipeline reliability** (10): required artifacts present, no step errors

## 3.2 New artifact schema

Add evaluator artifact fields:
- `kpi_breakdown`
- `overall_score`
- `risk_level` (`low|medium|high`)
- `recommendations[]`
- `evidence_paths[]`

## 3.3 Files to implement

- `src/careeros/phase3/evaluator_v2.py` (new)
- `src/careeros/phase3/next_steps.py` (wire v2 call)
- `apps/api/main.py`
  - add `POST /p24/evaluator/run_v2`
  - add `GET /p24/evaluator/latest?run_id=...`
- `tests/integration/test_p24_evaluator_v2.py` (new)

## 3.4 Example endpoint contracts

`POST /p24/evaluator/run_v2`
```json
{
  "run_id": "demo_run",
  "weights": {
    "match_quality": 30,
    "guardrails_quality": 25,
    "approval_quality": 20,
    "package_quality": 15,
    "pipeline_reliability": 10
  }
}
```

`GET /p24/evaluator/latest?run_id=demo_run`
- returns latest evaluator v2 artifact JSON.

---

## 4) Parser Agent v1 (next concrete implementation)

## 4.1 Scope

Replace deterministic stub with real extraction pipeline:
- TXT: direct text
- PDF: `pypdf` extraction
- DOCX: `python-docx`
- optional scanned PDF/image OCR: `tesseract` bridge

## 4.2 Files to implement

- `src/careeros/agents/parser_v1.py` (new)
- `apps/api/main.py`:
  - upgrade `POST /agents/parser/extract`
  - add `POST /agents/parser/ocr_extract`
- `tests/integration/test_parser_v1.py` (new)

## 4.3 Output contract

```json
{
  "status": "ok",
  "agent": "parser",
  "source_type": "pdf|docx|txt|image",
  "extracted_text": "...",
  "sections": {"skills": [], "experience": [], "education": []},
  "char_count": 1234,
  "warnings": []
}
```

---

## 5) P25 goal: real free-stack automation (no paid OpenAI)

P25 should focus on **free/open-source runtime** integrations.

## 5.1 LLM/model providers (free-first)

- **Ollama local models** (primary default)
  - `llama3.1:8b-instruct` (general generation)
  - `mistral:7b-instruct` (fast draft)
  - `qwen2.5:7b-instruct` (alternative)
- **Hugging Face open models** (fallback)
  - inference endpoints or local model download
- **Embeddings**
  - `sentence-transformers/all-MiniLM-L6-v2` (free)
- **OCR/CV**
  - `tesseract` (OCR)
  - optional `easyocr`

## 5.2 Orchestration/tools

- Keep **LangGraph** for stateful orchestration
- CrewAI optional for role abstraction if needed later
- MCP for tool contracts only when tools become external services

## 5.3 P25 automation targets

- Automated model routing (local-first)
- Automated parser + OCR extraction
- Automated connector ingestion (API/import sources)
- Automated evaluator v2 scoring per run
- Keep human-in-loop approval gate mandatory for sensitive actions

---

## 6) P25 implementation sequence (recommended)

1. Add provider config (`OLLAMA_BASE_URL`, model names, embedding model)
2. Implement parser_v1 + OCR path
3. Implement evaluator_v2 and scoring
4. Add generator model router (ollama first, HF fallback)
5. Add connector adapters (CSV/API)
6. Add observability artifacts + regression tests

---

## 7) Command checklist for developer

```bash
# sync
git fetch origin --prune
git checkout phase3-dev
git pull --rebase origin phase3-dev

# tests
pytest -q
pytest -q tests/unit tests/integration

# run API/UI
scripts/run_phase2_app.sh api
scripts/run_phase2_app.sh ui

# generate architecture visuals
python scripts/plot_phase3_flow.py
```
