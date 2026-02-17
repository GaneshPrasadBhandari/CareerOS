# CareerOS Codex Continuation Context (as of 2026-02-17)

Use this file when you start a fresh Codex chat so work continues from current state (not from scratch).

---

## 1) Current reality summary

- Production API health is **ok** on Render.
- `phases/status` shows `P1..P24 = ready`, `P25 = in_progress`.
- Streamlit URL responds but currently redirects to Streamlit auth flow (HTTP 303), which is expected for private/shared-app auth mode.
- Recent work added cloud-safe defaults, artifact open/read endpoints, feedback capture endpoints, and dynamic summary fallback (Ollama -> HF -> deterministic fallback).

---

## 2) Branch + commit baseline

Current working branch used in Codex: `work`.

Key latest commits:
- `e57237d` Harden cloud defaults and dynamic LLM fallback for Render deployments
- `e7ee659` Add automation scaffolding, feedback capture, artifact access APIs, and 6-day launch roadmap
- `5de676c` prior next_steps update

If you merge to `main`, this context assumes `main` includes at least `e7ee659` + `e57237d`.

---

## 3) What was implemented recently

### Cloud/hosting behavior
- Streamlit defaults backend URL from `st.secrets['API_URL']` or `st.secrets['BACKEND_URL']`, else fallback to Render API URL.
- UI surfaces LLM provider/tier/status after P25 run.

### Fallback model routing
- `src/careeros/orchestration/router.py`:
  - Tier 1: local Ollama
  - Tier 2: HuggingFace inference API (token-based)
  - Tier 3: deterministic fallback summary (returns status `ok` with warning)

### Artifact visibility and feedback loop
- API endpoints:
  - `GET /artifacts/open?path=...`
  - `GET /artifacts/read?path=...`
  - `POST /feedback/submit`
  - `GET /feedback/list`
  - `POST /feedback/employer_signal`
- Safe path handling for artifact endpoints limited to `outputs/`, `exports/`, `data/` roots.

### Structure scaffolding for next work
- Added directories:
  - `src/careeros/agents/`
  - `src/careeros/orchestration/`
  - `src/careeros/integrations/`
  - `src/careeros/feedback/`

---

## 4) What is NOT fully done yet (important)

1. Full top-8 job portal connectors (compliance-safe) are not complete.
2. Full ATS country-specific end-to-end resume/cover outputs are not complete.
3. Auto-apply/email/interview scheduling with strict human gate per sensitive action is not complete end-to-end.
4. Feedback-to-retraining closed loop is scaffolded but not fully productionized.
5. P25 remains `in_progress` in API phase status.

---

## 5) Recommended sync strategy now

If you are using `main` as active branch now:

```bash
# from local repo
git checkout main
git pull --rebase origin main

# merge work branch changes if not yet merged
git merge work

git push origin main
```

Then update `phase3-dev` to keep it aligned:

```bash
git checkout phase3-dev
git pull --rebase origin phase3-dev
git merge origin/main
git push origin phase3-dev
```

If merge conflicts appear, resolve in this order:
1) keep cloud-safe URL default in `apps/ui/Home.py`
2) keep `router.py` tiered fallback logic
3) keep artifact + feedback endpoints in `apps/api/main.py`

---

## 6) Immediate smoke tests after merge

Run these from your machine (not this Codex runner):

```bash
curl -sS https://careeros-backend-d9sc.onrender.com/health
curl -sS https://careeros-backend-d9sc.onrender.com/phases/status
curl -sS "https://careeros-backend-d9sc.onrender.com/feedback/list?limit=5"
```

For UI:
- Open: `https://career-os-final-test.streamlit.app/`
- Verify API URL defaults to Render backend.
- Run P25 upload flow and verify:
  - response JSON shows `llm_summary.provider` and `llm_summary.tier`
  - artifact links open/read correctly.

---

## 7) Next 6-day delivery focus (execution order)

Day 1-2:
- parser hardening for mixed resume inputs (pdf/docx/txt/linkedin text)
- persistent storage strategy for uploads/artifacts

Day 3-4:
- job connectors wave 1 + wave 2 (toward top-8)
- dedupe + normalization + explainability metadata
- strict HITL gates for apply/send/schedule actions

Day 5:
- ATS country template output (`US_ATS`, `UK_STANDARD`, `EUROPASS` baseline)
- full resume + full cover letter doc export (pdf/docx)

Day 6:
- feedback + employer signals into evaluator
- quality thresholds + fallback monitoring
- beta-readiness checklist

Day 7:
- controlled user beta release
- collect feedback via in-app form
- daily patch loop

---

## 8) Copy/paste prompt for your next fresh Codex chat

```text
We are continuing CareerOS from existing state (not from scratch).
Read docs/runbooks/CODEX_CONTINUATION_CONTEXT_2026-02-17.md first and follow it as baseline.
Current production URLs:
- UI: https://career-os-final-test.streamlit.app/
- API: https://careeros-backend-d9sc.onrender.com
Focus now: execute Day-1/Day-2 tasks from continuation context with tests and commits.
```

---

## 9) Render config notes

- Streamlit secrets should contain:

```toml
API_URL = "https://careeros-backend-d9sc.onrender.com"
```

- If Ollama is unavailable on Render, Tier-3 deterministic fallback still returns summary payload so user flow remains intact.

