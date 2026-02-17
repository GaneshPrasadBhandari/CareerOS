# 04_User_Journeys_and_Acceptance_Criteria_new_version.md
# CareerOS — Storytelling + User Journeys + Acceptance Criteria (L1 → L9)
Project: CareerOS Agentic AI Capstone  
Doc Type: Product Story + Testable Requirements (Seminar/Startup-ready)  
Version: v2.0 (Feb 2026)

---

## 0) Why this file exists
This single document does three jobs:
1) **Storytelling** (seminar + demo + investor/startup narrative)
2) **Architecture mapping** (Layers L1 → L9, stagewise flow)
3) **Acceptance criteria** (testable requirements that prove it’s real)

---

# 1) The story: Tanish and Sita (CareerOS in the real world)

> Note: You mentioned “Tanish and Sita” exists in your earlier uploaded docs. I don’t have that text visible right now, so I’m using a clean, realistic version that matches CareerOS’s architecture. If you paste your exact story paragraph later, I’ll align wording 1:1.

## Persona 1 — Tanish (the builder)
Tanish is a strong candidate on paper, but his job search is chaos.

He has:
- a resume that’s “fine” but generic,
- 50 saved job links,
- inconsistent messaging to recruiters,
- and the biggest risk: he starts adding skills to match jobs (because everyone does).

Tanish doesn’t need another chatbot.
He needs a **career execution engine** that:
- ranks jobs correctly,
- creates artifacts fast,
- and prevents false claims.

## Persona 2 — Sita (the optimizer)
Sita is disciplined and strategic. She’s not applying everywhere.
She’s applying to the **right roles** with **repeatable quality**.

Her pain:
- tailoring takes time,
- interview prep is inconsistent,
- and she can’t track what worked vs didn’t.

Sita needs a system that:
- runs a pipeline,
- versions artifacts,
- and learns from feedback loops.

## The “moment of truth”
Both Tanish and Sita face the same question:
**“Can I trust what this system generated enough to submit it to a real employer?”**

CareerOS is built to answer “yes” with evidence, logs, and approval gates.

---

# 2) The demo narrative (how to present CareerOS in any seminar)
You can present CareerOS in 6 minutes like this:

1) “We ingest your career evidence.”
2) “We interpret job requirements as structured signals.”
3) “We filter and rank jobs with explainability.”
4) “We generate a job-specific application package, grounded in proof.”
5) “We block unsupported claims.”
6) “We export a versioned bundle with an audit trail.”

That’s why CareerOS is a **product**, not a prompt.

---

# 3) L1 → L9 architecture mapping with story flow
This section is written so you can literally narrate it while demoing.

---

## L1 — User & UX Layer (Story: Tanish & Sita open CareerOS)
### What happens
Tanish uploads his resume and selects constraints: “Remote only, GenAI roles.”
Sita uploads her resume and sets: “Hybrid OK, target: ML Engineer.”

### Outputs (Artifacts)
- `outputs/intake/intake_bundle.json`
- `outputs/intake/resume_original.pdf`

### Acceptance criteria
- **AC-L1-1:** intake captures role targets + constraints + preferences
- **AC-L1-2:** intake prevents missing critical fields (location, role, seniority)

---

## L2 — Input & Connectors Layer (Story: bringing job posts into the system)
### What happens
Tanish pastes 3 job posts.
Sita pastes 5 job posts (or URLs).

### Outputs
- `outputs/jobs/job_{id}_raw.txt`

### Acceptance criteria
- **AC-L2-1:** each job is normalized into clean text
- **AC-L2-2:** resume is stored as a versioned artifact
  - `artifacts/raw/resume_v1.pdf`

---

## L3 — Parsing + Evidence Graph Layer (Story: CareerOS converts resume into “proof”)
### What happens
CareerOS parses their resumes into structured profiles.
Then it builds an **Evidence Graph**:
- every skill claim must link to a proof node (project, metric, repo, certification)

Tanish is tempted to add “Kubernetes expert.”
CareerOS flags it because there’s no evidence node.

### Outputs
- `outputs/profile/profile.json`
- `outputs/evidence/evidence_graph.json`
- `outputs/evidence/evidence_coverage.json`

### Acceptance criteria
- **AC-L3-1:** profile.json contains skills, roles, projects, timeline
- **AC-L3-2:** evidence_graph has ≥3 evidence nodes
- **AC-L3-3:** unsupported claims are detected and listed

---

## L4 — Knowledge + Retrieval (RAG) Layer (Story: CareerOS understands the jobs)
### What happens
CareerOS converts job text into structured requirements:
- must-have vs nice-to-have
- tools, frameworks
- seniority signals
- responsibilities

Optional: it retrieves templates (STAR answers, cover letter patterns).

### Outputs
- `outputs/jobs/job_{id}_requirements.json`
- (optional) `outputs/rag/retrieved_snippets_job_{id}.json`

### Acceptance criteria
- **AC-L4-1:** requirements include must-have and nice-to-have lists
- **AC-L4-2:** seniority inference exists with explanation notes

---

## L5 — Matching + Ranking Layer (Story: “why this job is #1”)
### What happens
CareerOS applies constraints first:
- Tanish’s “Remote only” rejects onsite-only roles.
- Sita’s “Hybrid OK” keeps more jobs.

Then it ranks eligible jobs using hybrid scoring:
- skill overlap
- project similarity
- seniority fit
- semantic similarity

### Outputs
- `outputs/match/eligibility_report.json`
- `outputs/match/ranked_jobs.json`

### Acceptance criteria
- **AC-L5-1:** at least one job rejected with clear reason when constraints apply
- **AC-L5-2:** ranked list includes a score breakdown per job

---

## L6 — Generation (LLM) Layer (Story: drafting artifacts, not inventing)
### What happens
For the top job:
- CareerOS generates tailored resume bullets
- and a cover letter draft

But it can only use evidence nodes.
So if Tanish lacks a proof for a skill, the bullet will not claim it.

### Outputs
- `outputs/gen/resume_bullets_job_{id}.md`
- `outputs/gen/cover_letter_job_{id}.md`

### Acceptance criteria
- **AC-L6-1:** bullets reference evidence ids
- **AC-L6-2:** letter includes at least 2 evidence references

---

## L7 — Guardrails + Governance Layer (Story: CareerOS blocks lies)
### What happens
This is the “trust layer.”

CareerOS runs claim validation:
- any unsupported claim gets blocked
- user gets a missing-evidence prompt
Then the user must approve before export.

### Outputs
- `outputs/guard/blocked_claims_job_{id}.json`
- `outputs/guard/validated_resume_bullets_job_{id}.md`
- `outputs/guard/validated_cover_letter_job_{id}.md`
- `outputs/guard/approval_job_{id}.json`
- `outputs/audit/audit_job_{id}.json`

### Acceptance criteria
- **AC-L7-1:** unsupported claims never pass validation
- **AC-L7-2:** export cannot proceed without approval artifact
- **AC-L7-3:** audit log includes ranking + validation summary

---

## L8 — Workflow + Packaging Layer (Story: the “real product” moment)
### What happens
Tanish clicks export.
CareerOS creates a job package folder:
- versioned resume bullets
- cover letter
- audit file (why this job, what evidence used)

Sita uses packages to track what worked and iterate.

### Outputs
- `exports/{company}_{role}_{date}/resume_v1.md`
- `exports/{company}_{role}_{date}/cover_letter_v1.md`
- `exports/{company}_{role}_{date}/audit.json`

### Acceptance criteria
- **AC-L8-1:** bundle structure is consistent every run
- **AC-L8-2:** versions never overwrite (suffix `_v2`, timestamp)

---

## L9 — Platform Ops Layer (Story: startup-grade engineering)
### What happens (capstone → startup evolution)
CareerOS becomes operational:
- experiment tracking (MLflow)
- artifact/data versioning (DVC)
- CI/CD (GitHub Actions)
- Docker + Kubernetes
- monitoring (Grafana)
- evaluation & drift (Evidently)
- optional Kafka for event-driven pipeline scaling

### Outputs
- MLflow run logs
- DVC tracked artifacts
- CI/CD build artifacts
- monitoring dashboards
- evaluation reports

### Acceptance criteria
- **AC-L9-1:** all pipeline steps are logged
- **AC-L9-2:** tests run on every PR
- **AC-L9-3:** deterministic demo mode supported (reproducible outputs)

---

# 4) Seminar-grade closing (what you say in 20 seconds)
CareerOS is built on a simple rule:
**If an AI system can’t explain its actions and prove its claims, it shouldn’t generate career-critical content.**

Tanish gets speed without risk.
Sita gets quality with repeatability.
And the system is designed like a startup product:
governed, versioned, auditable, and scalable.

---

# 5) One-slide summary you can copy into PPT
**CareerOS Pipeline**
L1 Intake → L2 Ingest → L3 Evidence Graph → L4 Requirements (RAG) → L5 Gate+Rank → L6 Generate → L7 Validate+Approve → L8 Export → L9 Operate+Monitor

**Key Differentiator:** “No evidence, no claim” enforced at runtime.
