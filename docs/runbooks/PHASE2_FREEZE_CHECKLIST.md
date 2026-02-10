# CareerOS Phase 2 Freeze — Safe-to-Sync Checklist

## Goal
Freeze **Phase 2 (P13–P19)** in a demo-ready state while keeping **Phase 1 (P1–P12)** stable.

---

## 1) old `mainold.py` vs new `main.py` endpoint matrix

### A. Endpoints present in `mainold.py` and still present in `main.py` (kept)
- `GET /`
- `GET /health`
- `GET /version`
- `POST /intake`
- `POST /profile`
- `GET /debug/error`
- `POST /jobs/ingest`
- `POST /match/run`
- `POST /rank/run`
- `POST /generate/package`
- `POST /guardrails/validate`
- `POST /export/package`
- `POST /apply/update_status`
- `GET /applications/list`
- `GET /applications/metrics`
- `GET /applications/{application_id}`
- `POST /followups/generate`
- `GET /followups/latest`
- `POST /notifications/generate`
- `GET /notifications/latest`
- `POST /orchestrator/run`

### B. New endpoints in `main.py` (Phase 2+ additions)
- `GET /tools` (P13)
- `POST /runs/init` (P13)
- `POST /runs/execute_plan` (P14)
- `POST /p17/grounding` (P17)
- `POST /p18/guardrails_v2` (P18)
- `POST /p19/state/new` (P19)
- `GET /p19/state/latest` (P19)
- `GET /phases/status` (phase visibility)

### C. Router-mounted endpoints (P15)
- `GET /orchestrator/current_state`
- `POST /orchestrator/approve`
- `POST /orchestrator/reject`

---

## 2) UI ↔ API alignment check (`apps/ui/Home.py`)

The Streamlit home page is aligned with API routes for:
- Phase 1 / base flow: health/version + P1→P12 calls.
- Human-in-the-loop (P15): current_state/approve/reject.
- P17: grounding call (`/p17/grounding`).
- P18: citation guardrails (`/p18/guardrails_v2`).
- P19: state create/load (`/p19/state/new`, `/p19/state/latest`).
- Phase summary: `/phases/status`.

---

## 3) Demo freeze gates (must pass before syncing)

### Gate A — API health and route availability
- [ ] `GET /health` returns `200`.
- [ ] `GET /phases/status` returns P1..P19 as available/ready.

### Gate B — Core pipeline still works (P1→P12)
- [ ] Intake/profile/job/match/rank/generate/guardrails/export paths are callable.
- [ ] Orchestrator P12 endpoint still works: `POST /orchestrator/run`.

### Gate C — Phase 2 checks
- [ ] P17 endpoint returns grounded package metadata.
- [ ] P18 endpoint blocks packages with missing citations and passes complete ones.
- [ ] P19 endpoint creates typed state and latest-state endpoint can fetch it.

### Gate D — UI demo readiness
- [ ] Streamlit Home loads and all phase sections/buttons render.
- [ ] P18 + P19 sections visible and callable.

---

## 4) Recommended demo command sequence

```bash
PYTHONPATH=src uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
PYTHONPATH=src streamlit run apps/ui/Home.py --server.address 0.0.0.0 --server.port 8501
```

Then run this quick validation:

```bash
PYTHONPATH=src pytest -q tests/integration/test_api_health.py tests/unit/test_p17_grounded_generation.py tests/unit/test_p14_execute_plan_smoke.py
```

---

## 5) Decision

**Safe to sync for Phase 2 demo** if all four gates above pass.

### Important note before Phase 3
For Phase 3 (automation + LLM + agentic + third-party tools), this freeze should be treated as the stable baseline. Any new LLM/tool integrations should be feature-flagged (or route-gated) so the P1→P19 demo path remains reproducible.
