# CareerOS 6-Day Automation Execution Plan (V2)

## Goal
Ship a beta-ready automated platform for students/professionals: daily top jobs, tailored resume+cover letter, HITL safety, analytics, and feedback learning loop.

## Day 1 — Discovery + Parsing + Governance
- Multi-role job discovery (3-5 role choices, daily top-20 cap).
- Resume/profile ingestion from text, upload, LinkedIn/web URL.
- Privacy mode: PII redaction + artifact governance checks.

## Day 2 — Matching Confidence + HITL
- Confidence scoring policy with reasons.
- Human-approval gates for low confidence or non-pass guardrails.
- UI confidence panel and approval rationale.

## Day 3 — Tailored Output Quality
- Full tailored resume sections (summary, skills, experience/projects highlights).
- Role/job-specific full cover letter generation.
- Export validation for DOCX/PDF outputs.

## Day 4 — Storage + Vector Foundation
- Define storage topology (`outputs/`, `exports/`, DB).
- Add optional vector backend toggle (`none/chroma/qdrant`) and embedding model policy.
- Add retrieval quality checks and traceability metrics.

## Day 5 — Analytics + Feedback Learning
- Capture user feedback, employer signals, acceptance outcomes.
- Add analytics slices by role/source/guardrail/HITL state.
- Route learning signals into evaluator score adjustments.

## Day 6 — Beta Hardening + Release Readiness
- End-to-end Render smoke tests (API+UI+P25).
- Reliability checklist: retries, degradations, fallback policies.
- Publish tester guide and monitor daily triage dashboard.

## Success Criteria
- Top-20 daily jobs generated for selected roles and location.
- Tailored resume and cover letter are job-specific and downloadable.
- HITL confidence and reasons visible before sensitive actions.
- Feedback is stored and used for evaluator/analytics improvements.
