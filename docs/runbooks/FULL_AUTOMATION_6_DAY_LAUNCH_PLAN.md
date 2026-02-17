# CareerOS Full Automation 6-Day Launch Plan (Day 7 User Beta)

## What has been automated so far
- End-to-end P25 API path for parse -> ingest -> match -> rank -> generate -> guardrails -> summary.
- LangGraph pipeline node chain is present with deterministic fallback.
- Human-approval endpoints exist (P22).
- Tracking, followups, notification drafts, and system health snapshots exist.
- Upload-based P25 route exists for real resume/job files.

## New architecture structure (implemented)
- `src/careeros/agents/`
  - parser, connector, matcher, ranker, generator, guardrails, approval, followup, notification, scheduler wrappers
- `src/careeros/orchestration/`
  - `langgraph_graph.py`, `policies.py`, `router.py`, `state.py`
- `src/careeros/integrations/`
  - `job_boards/`, `email/`, `calendar/`, `storage/`, `mcp_client/` scaffolds
- `src/careeros/feedback/`
  - feedback ingestion + employer outcome signal hooks

## Free-first model/tool policy (active)
### Tier 1 (default)
- Ollama local models (Llama/Qwen/Mistral)
- sentence-transformers embeddings
- Chroma/Qdrant local vector options
- Tesseract/pypdf/python-docx for document extraction

### Tier 2 (cheap fallback)
- Low-cost hosted inference only when local fails

### Tier 3 (premium)
- Paid premium models only for strict quality bottlenecks

## 6-day execution roadmap

### Day 1 (today) — foundation + visibility
1. Finalize architecture segregation (agents/orchestration/integrations/feedback folders).
2. Add feedback APIs and UI feedback form.
3. Add artifact open/read APIs so users can open generated files by path.
4. Add provider fallback router (tiered generation policy).

**Deliverables**
- New module layout in place.
- `/feedback/submit`, `/feedback/list`, `/feedback/employer_signal` running.
- `/artifacts/open` and `/artifacts/read` running.
- P25 summary route fallback updated to dynamic policy.

### Day 2 — parser + storage hardening
1. Harden parser for PDF/DOCX/TXT/LinkedIn text blobs.
2. Add persistent upload storage strategy (local now, object storage ready switch).
3. Add tests for parse edge cases and path access safety.

### Day 3 — top-job-source connector wave 1
1. Build compliant connectors (API-first) for first 3 job sources.
2. Normalize jobs into common schema and dedupe pipeline.
3. Add explainable reason fields for every recommended job.

### Day 4 — connectors wave 2 + apply intent gates
1. Add remaining target job sources up to top 8 (compliance-safe).
2. Add explicit human approval gates before apply/email/send actions.
3. Add interview scheduling suggestion + approval workflow.

### Day 5 — ATS country templates + full docs output
1. Add country template profiles (`US_ATS`, `UK_STANDARD`, `EUROPASS` baseline).
2. Build complete resume + cover letter (not only bullets) for selected job.
3. Ensure PDF/DOCX outputs are generated and downloadable.

### Day 6 — feedback loop + quality lock
1. Connect feedback data and employer outcome signals to evaluator inputs.
2. Add quality thresholds and fallback escalation rules.
3. End-to-end regression run + beta checklist + monitoring checks.

## Day 7 — user beta rollout
1. Deploy API + UI with stable public link.
2. Invite user cohort and collect feedback through in-app feedback form.
3. Daily triage dashboard: failures, model fallbacks, acceptance rates.
4. Patch priority issues and re-run release smoke tests.

## Dynamic fallback behavior standard
For each LLM-powered step:
1. Try Tier 1 local provider.
2. If unavailable/error -> Tier 2 cheap hosted provider.
3. If still unavailable -> Tier 3 premium provider only when configured; otherwise graceful degraded output with retry guidance.

## Success criteria for “fully automated beta”
- User can upload resume/job inputs and get complete tailored outputs automatically.
- All recommendations have explainable reasons.
- Human approval is mandatory before sensitive apply/send/schedule actions.
- Outputs are visible, downloadable, and traceable by artifact endpoints.
- Feedback loop is live and captured for model/process improvement.


## Render deployment links (current)
- UI: `https://career-os-final-test.streamlit.app/`
- API: `https://careeros-backend-d9sc.onrender.com`
- Streamlit `secrets.toml` should include: `API_URL = "https://careeros-backend-d9sc.onrender.com"`
