# 04_User_Journeys_and_Acceptance_Criteria.md
# CareerOS — User Journeys & Acceptance Criteria (Testable Requirements)
Project: CareerOS Agentic AI Capstone  
Doc Type: Requirements + Acceptance Criteria  
Version: v1.1 (Feb 2026)

---

## 0) Why this file exists
This document turns features into **testable requirements**.  
In capstone language: “We built a system with acceptance criteria, not a demo.”

Each journey maps to:
- feature pipeline steps
- required artifacts
- acceptance tests

---

# Journey 1 — Build Candidate Evidence Profile
## User story
As a user, I want to upload my resume and constraints so CareerOS can build a structured profile and evidence graph.

## Feature pipeline
F1 → F4 → F5 → F6

## Inputs
- **[USER]** resume.pdf
- **[USER]** constraints/preferences

## Required artifacts
- `outputs/intake/intake_bundle.json`
- `outputs/profile/profile.json`
- `outputs/evidence/evidence_graph.json`

## Acceptance criteria
- **AC1:** intake_bundle.json contains role target + remote/location constraints  
- **AC2:** profile.json includes skills + experience timeline + education  
- **AC3:** evidence_graph.json contains >= 3 evidence nodes  
- **AC4:** evidence_coverage.json identifies unsupported claims (if any)

---

# Journey 2 — Ingest Jobs and Extract Requirements
## User story
As a user, I want to paste job posts so CareerOS can extract structured requirements.

## Feature pipeline
F3 → F7

## Required artifacts
- `outputs/jobs/job_{id}_raw.txt`
- `outputs/jobs/job_{id}_requirements.json`

## Acceptance criteria
- **AC1:** job requirements includes must-have and nice-to-have sections  
- **AC2:** requirements contain at least: skills/tools + responsibilities  
- **AC3:** extraction completes under 30 seconds per job (capstone target)

---

# Journey 3 — Eligibility Filtering (Constraints Gate)
## User story
As a user, I want jobs filtered based on my constraints.

## Feature pipeline
F9 (consumes outputs from F1 and F7)

## Required artifacts
- `outputs/match/eligibility_report.json`

## Acceptance criteria
- **AC1:** each job is marked eligible/ineligible  
- **AC2:** each ineligible job includes at least one explicit reason  
- **AC3:** override (if used) is recorded (manual flag)

---

# Journey 4 — Rank Jobs with Explainability
## User story
As a user, I want a ranked shortlist with clear reasons.

## Feature pipeline
F10 (consumes F6, F7, F9)

## Required artifacts
- `outputs/match/ranked_jobs.json`

## Acceptance criteria
- **AC1:** ranked list produced for eligible jobs  
- **AC2:** each ranked job includes score breakdown factors  
- **AC3:** top job includes evidence references (why fit)  
- **AC4:** ranking explainable in under 60 seconds using outputs

---

# Journey 5 — Generate Evidence-Backed Application Artifacts
## User story
As a user, I want tailored bullets and a cover letter without false claims.

## Feature pipeline
F11 → F12 → F14

## Required artifacts
- `outputs/gen/resume_bullets_job_{id}.md`
- `outputs/gen/cover_letter_job_{id}.md`
- `outputs/guard/blocked_claims_job_{id}.json`
- `outputs/guard/validated_resume_bullets_job_{id}.md`
- `outputs/guard/validated_cover_letter_job_{id}.md`

## Acceptance criteria
- **AC1:** generated bullets are grounded in evidence_graph ids  
- **AC2:** unsupported claims are blocked and logged  
- **AC3:** validated outputs exist and are the only ones exportable

---

# Journey 6 — Approve and Export Package
## User story
As a user, I want to approve outputs and export a job-specific bundle.

## Feature pipeline
F15 → F16 → F17

## Required artifacts
- `outputs/guard/approval_job_{id}.json`
- `outputs/audit/audit_job_{id}.json`
- `exports/{company}_{role}_{date}/...`

## Acceptance criteria
- **AC1:** export cannot happen without approval artifact  
- **AC2:** export folder contains validated resume + letter + audit  
- **AC3:** package naming convention consistent  
- **AC4:** audit log includes ranking + validation summary

---

# System-wide Non-Functional Requirements (capstone-grade)
- **NFR1:** all steps produce structured logs in `/logs/`  
- **NFR2:** errors produce structured exception traces  
- **NFR3:** deterministic mode option for reproducible demos  
- **NFR4:** artifacts never overwrite; versions are suffixed (`_v2`, timestamps)

---

# How to use this in class
When presenting, you say:
“This demo validates Journey 4, AC1–AC4.”
It sounds like a real product team and makes grading easier.
