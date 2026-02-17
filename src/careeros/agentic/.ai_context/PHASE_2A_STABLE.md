# 🛡️ Phase 2A: Agentic Foundation (P13 - P14)

## 🏗️ Transition: From Sequential to Reasoning
Phase 2A marks the shift from a linear script (P12) to an **Agentic Orchestrator**. We introduced a State Model to handle non-linear flow and a Tool Registry so agents can "call" our deterministic Phase 1 functions as needed.

## ✅ Completed Phase 2A Stages
| Stage | Artifact Produced | Location | Core Responsibility |
| :--- | :--- | :--- | :--- |
| **P13** | `StateModel` / Vector DB | `outputs/state/` | Persistent memory to track the "Context" across agent loops and semantic search. |
| **P14** | `tool_registry.py` | `src/orchestrator/` | Standardizes Phase 1 modules (Matcher, Parser, etc.) into executable tools for the CEO/Director agents. |

---

## 🛠️ Stage Deep-Dive

### P13: Persistent State & Semantic Memory
- **State Model:** A unified Pydantic object that stores the current `run_id`, active `IntakeBundle`, and all generated `MatchResults`. 
- **Vector DB (ChromaDB):** Converts the `EvidenceProfile` into embeddings. 
- **Why it matters:** Allows the system to understand that "Python Developer" matches "Backend Engineer" even if the keywords aren't identical (Semantic Matching).
- **Mapping:** Arch L8 (Memory & Models).

### P14: Tool Registry & Agentic Orchestrator
- **The Tool Registry:** A decorator-based system that wraps your stable P1-P12 functions. 
- **Agentic Loop:** Instead of a hardcoded sequence, the Orchestrator uses a "Reasoning Loop" (LangGraph/CrewAI style) to decide: *"Do I have enough job data? If no, call the Sourcing Tool."*
- **The "Baton":** Every tool call consumes a state and returns an updated state, ensuring the "Artifact Contract" remains intact.
- **Mapping:** Arch L2 (Strategic Orchestration).

---

## 🚦 Operational Rules for P15+
1. **State Persistence:** The `StateModel` must be saved to `outputs/state/state_{run_id}.json` at every step to allow for "Replay" and "Resume" capabilities.
2. **Tool Hermeticity:** Tools are forbidden from modifying external state directly; they must only return values to the Orchestrator.
3. **Human Intercept:** P14 established the routing logic that will now be used by **P15** to trigger the `WAIT_FOR_USER` state.