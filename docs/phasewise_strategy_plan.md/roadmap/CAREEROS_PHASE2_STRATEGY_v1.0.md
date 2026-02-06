roadmap/CAREEROS_PHASE2_STRATEGY_v1.0.md

CAREEROS_PHASE2_STRATEGY_v1.0.md
BLUF
Phase 1 delivered a fully working artifact-first CareerOS pipeline (P1→P12) with governance proof (P7 blocks unsupported claims) and one-click orchestration (P12 runs P6→P11 end-to-end).
Phase 2 upgrades the system from “manual pipeline” to agentic execution aligned to Architecture Layers L2/L3/L4/L5/L8/L9, while keeping all Phase-1 determinism + auditability intact.

Phase 1 Completed (Proof of Engineering + Governance)
What Phase 1 is
A deterministic, testable pipeline where every stage writes artifacts to disk, enabling:

repeatable runs

inspection/debugging

audit logs

safe generation without hallucination

guardrails enforcement

What we built (P1 → P12)
P1 Intake → writes outputs/intake/intake_bundle_v1_*.json
P2 Parsing → writes outputs/profile/profile_v1_*.json (EvidenceProfile)
P3 Job Ingestion → writes outputs/jobs/job_post_v1_*.json
P4 Matching → writes outputs/matching/match_result_v1_*.json
P5 Ranking → writes outputs/ranking/shortlist_v1_*.json
P6 Generation → writes exports/packages/application_package_v1_*.json
P7 Guardrails → writes outputs/guardrails/validation_report_v1_*.json (pass/blocked)
P8 Export + Tracking → writes exports/submissions/... and appends ledger outputs/apply_tracking/applications_v1.jsonl
P9 Analytics → reads ledger, provides funnel metrics + list views
P10 Followups → writes outputs/followups/followups_v1.json
P11 Notifications → writes outputs/notifications/drafts_v1.json
P12 Orchestrator → one-click run of P6→P11 with step-by-step StepResult trace; writes outputs/orchestrator/orchestrator_run_v1_*.json

Key Phase-1 proof points
✅ Full manual workflow works in Streamlit + API

✅ Unit tests run under PYTHONPATH=src pytest -q

✅ Guardrails rule GR001 blocks unsupported “skills”

✅ Tracking ledger persists state across runs

✅ Followups + draft generation built deterministically

✅ P12 orchestration shows a single JSON run summary + output artifacts

Phase 2 Goal
Convert Phase-1 pipeline into an agentic system where:

L2/L3 managers decide what to do next (plan + execute)

L4 agents operate via tools (functions) that call Phase-1 services

L5 approval gates become real “human-in-the-loop” checkpoints

L8 memory evolves from “latest artifact” → “retrieval + state”

L9 governance becomes enforced at runtime for every agent action

No Phase-2 change is allowed to break Phase-1 determinism.
Phase-1 remains your “safe mode.”

Phase 2 Architecture Mapping (What we implement)
Arch L2 — Orchestrator / Planner
decides which pipeline actions to run

maintains run state (what’s done, what’s next)

enforces stop conditions (blocked, missing info, approvals required)

Arch L3 — Managers
Career Strategy Manager (what roles to target, refine intake)

Job Operations Manager (ingest jobs, rank, pick targets)

Application Manager (generate package, validate, export, track)

Arch L4 — Agents
Job Ingestion Agent

Match + Rank Agent

Tailor + Generate Agent

Guardrails Agent

Followup Agent

Draft Writing Agent (still deterministic in Phase 2; LLM later)

Arch L5 — Human Approval Gates
must approve before export/apply actions

approval artifacts logged and persisted

Arch L8 — Memory & Models
memory object (state model) containing:

latest intake/profile/shortlist

job targets

last validation status

last application_id and followups

later: retrieval augmentation from vector DB (Phase 3)

Arch L9 — Governance/Ops
enforce guardrails on any generated text before it becomes an artifact

immutable logs and policy checks attached to every action

Phase 2 Deliverables (Stepwise Plan)
P13 — State Model + Tool Registry (foundation)
Deliver:

State Pydantic model representing current workflow state

Tool wrappers around existing Phase-1 services (P1–P12 functions)

state transitions that store artifact paths + statuses

Why this matters:
Agents need structured state + tools. Otherwise it becomes “random LLM calls.”

P14 — Agentic Orchestration (deterministic first)
Choose one orchestrator framework:

Option A: LangGraph (recommended for state machines)

Option B: CrewAI (good for role-based agents)

Option C: MCP orchestration (later)

Deliver:

a graph/flow that runs:

ingest → rank → generate → guardrails → export → tracking → followups → drafts

same outputs as Phase-1, but now invoked by orchestrator state machine

Guardrail rule:
If blocked, orchestrator must stop and request human approval.

P15 — Human Approval Gate (real L5)
Deliver:

Approval schema: who approved, when, what artifacts approved

API endpoint: /approval/submit

Streamlit UI gate: approve/reject after guardrails pass

Orchestrator: export only allowed if approved

P16 — Reliability + Observability upgrade
Deliver:

standardized structured event log per step (already partially done)

run trace persisted for every agent run

“replay run” ability from orchestrator output JSON

P17 — LLM integration (still grounded)
Only after P13–P16 are stable:

LLM used for:

better bullet rewriting

cover letter improvements

outreach message quality

with hard constraints:

must reference evidence

guardrails enforced

citations / provenance added later

Phase 2 Testing Strategy (mandatory)
Unit test per agent tool wrapper

Integration test: “agentic run returns ok/blocked”

Regression tests ensure Phase-1 endpoints still work

Commands:

PYTHONPATH=src pytest -q
PYTHONPATH=src uvicorn apps.api.main:app --reload --port 8000
CAREEROS_API_URL=http://127.0.0.1:8000 streamlit run apps/ui/Home.py
Demo workflow (Phase 2)
run agentic orchestrator “one click”

show:

step-by-step state transitions

artifacts written

logs show enforced governance

blocked claim causes orchestrator to stop and request approval

Next step to start Phase 2 (action)
Implement P13:

State model (Pydantic)

Tool registry wrapping existing services

Minimal orchestrator that calls tools sequentially (no LLM)

Git push discipline
code only committed

outputs/ and exports/ stay gitignored

runbooks and roadmap docs are committed

Next Steps (what you do now)
Fix integration test import (mainold → main)

Commit Phase-1 fixes + P12 unit test

Start Phase-2 P13: state + tool registry