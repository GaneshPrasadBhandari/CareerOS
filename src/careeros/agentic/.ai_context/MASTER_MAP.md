# 🗺️ CareerOS: Master Architecture & Pipeline Map (V4)

## 🎯 Current Mission
- **Status:** Phase 1 (Deterministic Spine) Complete. 
- **Active Focus:** Phase 2 (Agentic Core) - Specifically **P15: Human Approval Gate**.
- **Philosophy:** "Explainability by Design". Every AI action must be traceable to the Evidence Profile.


## 👤 2. Persona Context (The "Why")
- **Tanish (The Builder):** Needs speed but lacks tracking. The system must prevent him from "embellishing" skills to match jobs.
- **Sita (The Optimizer):** Strategic and disciplined. She needs repeatable quality and a system that learns from her outcomes.
- **The Moment of Truth:** "Can I trust this system enough to submit it to a real employer?" Every piece of code must support this trust.


## 🏛️ 9-Layer Architecture vs. Agent Hierarchy
| Layer | Name | Agent Role | Pipeline Stage | Key Feature |
| :--- | :--- | :--- | :--- | :--- |
| **L1** | Entry/UX | *Deterministic* | P1 | F1: Intake Wizard |
| **L2** | Strategic Orch | **CEO & Director** | P12-P14 | F9: Constraint Gate |
| **L3** | Tactical Mgmt | **Managers** | P4-P5 | F10: Job Ranking |
| **L4** | Generation | **Creators** | P18 | F11: Resume Tailoring |
| **L5** | Human Gate | **USER (Sita/Tanish)**| P15 | F16: Approval UI |
| **L6** | Execution | **Workers** | P8 | F17: Export Builder |
| **L7** | Analytics | **Analysts** | P31 | F23: Drift Detection |
| **L8** | Knowledge | *RAG System* | P3 | F6: Evidence Graph |
| **L9** | Governance | **Guardrails** | P7, P16 | F15: Audit Trace |

## 🤖 Agent Command Rules
1. **The C-Suite (L2):** The **CEO** plans the search strategy; the **Director** audits it against user constraints.
2. **Grounded Generation (L4):** Creator agents are forbidden from "fabricating" skills. They must use the **L8 Knowledge Layer** as the sole source of truth.
3. **The Safety Brake (L5):** No L6 Execution task can start without a validated `approval_artifact.json` from the user.