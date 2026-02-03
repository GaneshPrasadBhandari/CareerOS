# docs/architecture/ARTIFACT_FLOW_CONTRACTS.md
# CareerOS — Artifact Flow Contracts (Producers / Consumers / Purpose)
Project: CareerOS Agentic AI Capstone  
Owner: Ganesh Prasad Bhandari  
Doc Type: Data Contracts + Pipeline Artifacts  
Version: v1.0 (Feb 2026)

---

## 0) Purpose
This document defines the “contracts” between layers.  
Every artifact has:
- a producer (module/feature)
- a consumer (downstream module/feature)
- minimal schema expectations
- test requirements

Rule: **Agents and services may only communicate through these artifacts/contracts.**

---

## 1) Core artifacts (end-to-end)

### A1. Intake Bundle
- Path: `outputs/intake/intake_bundle.json`
- Produced by: L1 Intake (F1)
- Consumed by: L5 Constraint Gate (F9), L3 Parser (F5)
- Contains (minimum):
  - target_roles (list)
  - constraints: location/remote/salary/visa notes
  - links (optional): LinkedIn/GitHub
- Tests:
  - schema required fields present
  - constraints validated (enums/ranges)

### A2. Resume Raw (Versioned)
- Path: `artifacts/raw/resume_v{n}.pdf`
- Produced by: L2 Storage (F4)
- Consumed by: L3 Parser (F5)
- Tests:
  - file exists
  - hash recorded

### A3. Profile JSON
- Path: `outputs/profile/profile.json`
- Produced by: L3 Resume Parser (F5)
- Consumed by: Evidence Graph (F6), Ranker (F10)
- Contains (minimum):
  - skills (list)
  - experience timeline (roles with dates)
  - projects/achievements
- Tests:
  - schema validation
  - non-empty skills
  - timeline ordering valid

### A4. Evidence Graph
- Path: `outputs/evidence/evidence_graph.json`
- Produced by: Evidence Builder (F6)
- Consumed by: Ranker (F10), Generators (F11/F12), Validator (F14)
- Contains (minimum):
  - evidence_nodes (id, type, text, tags)
  - claim_to_evidence mapping (optional)
- Tests:
  - ≥3 evidence nodes
  - ids unique
  - coverage report exists

### A5. Job Raw Text
- Path: `outputs/jobs/job_{id}_raw.txt`
- Produced by: Job Ingest (F3)
- Consumed by: Requirements Extractor (F7)
- Tests:
  - non-empty
  - job_id format valid

### A6. Job Requirements
- Path: `outputs/jobs/job_{id}_requirements.json`
- Produced by: Requirements Extractor (F7)
- Consumed by: Gate (F9), Ranker (F10), Generators (F11/F12)
- Contains (minimum):
  - must_have (list)
  - nice_to_have (list)
  - responsibilities (list)
  - seniority (string)
- Tests:
  - must_have exists (can be empty but present)
  - seniority in allowed set

### A7. Eligibility Report
- Path: `outputs/match/eligibility_report.json`
- Produced by: Constraint Gate (F9)
- Consumed by: Ranker (F10)
- Contains (minimum):
  - job_id → eligible (bool)
  - reasons (list)
- Tests:
  - all jobs accounted for
  - ineligible must include at least one reason

### A8. Ranked Jobs
- Path: `outputs/match/ranked_jobs.json`
- Produced by: Hybrid Ranker (F10)
- Consumed by: UI Explain (F2), Generators (F11/F12), Audit (F16)
- Contains (minimum):
  - ranked list with scores
  - score_breakdown (per job)
- Tests:
  - scores numeric
  - breakdown fields present
  - ordering correct (descending)

### A9. Generated Resume Bullets
- Path: `outputs/gen/resume_bullets_job_{id}.md`
- Produced by: Generator (F11)
- Consumed by: Validator (F14), Export (F17)
- Contains (minimum):
  - bullets list
  - embedded evidence references
- Tests:
  - ≥5 bullets (for demo mode)
  - evidence refs included

### A10. Generated Cover Letter
- Path: `outputs/gen/cover_letter_job_{id}.md`
- Produced by: Generator (F12)
- Consumed by: Validator (F14), Export (F17)
- Tests:
  - non-empty
  - references ≥2 evidence nodes (for demo mode)

### A11. Blocked Claims Report
- Path: `outputs/guard/blocked_claims_job_{id}.json`
- Produced by: Claim Validator (F14)
- Consumed by: Audit (F16), UI display, Approval Gate (F15)
- Tests:
  - if blocked claims exist, each has reason + evidence_missing field

### A12. Validated Artifacts
- Paths:
  - `outputs/guard/validated_resume_bullets_job_{id}.md`
  - `outputs/guard/validated_cover_letter_job_{id}.md`
- Produced by: Validator (F14)
- Consumed by: Approval Gate (F15), Export (F17)
- Tests:
  - validated outputs exist even if no blocks (copy-through allowed)

### A13. Approval Artifact
- Path: `outputs/guard/approval_job_{id}.json`
- Produced by: Approval Gate (F15)
- Consumed by: Export (F17)
- Tests:
  - export must fail without this file

### A14. Audit Log
- Path: `outputs/audit/audit_job_{id}.json`
- Produced by: Audit (F16)
- Consumed by: UI Explain, export bundle, evaluation
- Contains (minimum):
  - run_id
  - input artifact references
  - ranking summary
  - validation summary
- Tests:
  - run_id exists
  - references point to real files

### A15. Export Bundle
- Path: `exports/{company}_{role}_{date}/...`
- Produced by: Package Builder (F17)
- Consumed by: user
- Contains (minimum):
  - validated resume bullets
  - validated cover letter
  - audit.json
- Tests:
  - export structure matches template
  - no overwrite policy (version suffix)

---

## 2) Deterministic demo mode contract
When `DEMO_MODE=true`, the system must:
- produce repeatable rankings with fixed config
- generate stable artifacts
- intentionally include one test case that triggers a blocked claim (guardrail proof)

---

## 3) Agentic mode contract
Agents may:
- read only from `outputs/` and `artifacts/`
- write only into the next expected artifact locations
- never bypass validator/approval/export contracts
