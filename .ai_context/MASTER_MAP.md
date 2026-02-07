# 🏗️ CareerOS: AI Context & Orchestration Map

## 🎯 Current Mission
**Current Stage:** Transitioning from Phase 1 (Deterministic) to Phase 2 (Agentic).
**Active Pipeline Point:** P15 (Human-in-the-loop Approval Gate).
**Primary Goal:** Implementing the L2 (C-Suite) Agent logic using LangGraph.

## 🏛️ The 9-Layer Architecture vs. Pipeline Stages
| Layer | Name | Status | Pipeline Stages | Agent Responsibility |
| :--- | :--- | :--- | :--- | :--- |
| **L1** | Entry/UX | ✅ DONE | P1 | Deterministic Logic |
| **L2** | Strategic Orch | 🏗️ BUSY | P12-P14 | **CEO (Planner) & Director (Reviewer)** |
| **L3** | Tactical Mgmt | ✅ DONE | P4-P5 | Manager Agents (Ranking/Matching) |
| **L4** | Generation | 🏗️ NEXT | P18 | Content Agents (Resume/Cover Letter) |
| **L5** | Human Gate | 🏗️ NEXT | P15 | **User Approval (The Brake)** |
| **L6** | Execution | 📅 TODO | P8 | Worker Agents (Apply/Submit) |
| **L7** | Analytics | 📅 TODO | P9, P31 | Feedback & Self-Learning |
| **L8** | Memory/Models | ✅ DONE | P3, P18 | RAG & Vector DB (Chroma) |
| **L9** | Governance | 🏗️ BUSY | P7, P16 | Guardrails & XAI (Explainability) |

## 🤖 Agent Hierarchy Rules
1. **CEO Agent (L2):** Receives the `EvidenceProfile` (L1) and generates a `SearchStrategy`.
2. **Director Agent (L2):** Must audit the `SearchStrategy` against `GuardrailPolicies` (L9).
3. **Manager Agents (L3):** Execute specific tactics (e.g., scoring 50 jobs).
4. **Worker Agents (L6):** Perform the high-volume tasks only AFTER **L5 Human Approval**.

## 🛠️ Tech Stack & Constraints
- **State Management:** LangGraph (Stateful Graph).
- **Communication:** Every step must produce a validated JSON artifact.
- **Grounding:** No agent can invent skills. Grounding source: `src/data/evidence_profile.json`.