# Phase 3 Simple Workflow + L1-L9 Mapping

This page explains **what is happening now** with concrete input/output examples.

## A) Current runtime workflow (today)

1. **P20 validate contract**
   - Input JSON:
     - `run_id`, `agent`, `objective`, `constraints`
   - Output JSON:
     - `status=ok/error`, normalized contract

2. **P21 dry run**
   - Input JSON: same P20 contract payload
   - Output JSON:
     - `status=ok`
     - artifact path like `outputs/phase3/dry_run_planner_*.json`

3. **P21 full graph run**
   - Input JSON:
     - `run_id`, optional `profile_path`, optional `job_path`, `top_n`
   - Graph nodes executed:
     - `load_context -> match -> rank -> generate -> guardrails`
   - Output JSON:
     - `match_path`, `shortlist_path`, `package_path`, `validation_report_path`, `validation_status`

---

## B) L1-L9 architecture alignment

- **L1 User/UI**: Streamlit Home actions and curl inputs.
- **L2 API**: `/phase3/readiness`, `/p20/contracts/validate`, `/p21/langgraph/dry_run`, `/p21/langgraph/run`.
- **L3 Orchestration**: LangGraph state machine in P21.
- **L4 Agents**: Context loader, matcher, ranker, generator, guardrails.
- **L5 Human-in-loop**: P22 approval node (next step).
- **L6 Execution/Tracking**: artifacts written to `outputs/` and logs.
- **L7 Analytics/Learning**: planned expansion in P24 evaluation harness.
- **L8 Memory/Models**: planned persistence/model upgrades in P23.
- **L9 Governance/Ops**: contract validation + guardrails + audit traces.

---

## C) What is automated now vs later

### Automated now
- Contract checks (P20)
- Orchestrated deterministic graph execution (P21)
- Matching/ranking/generation/guardrails pipeline

### Human-controlled now
- Any final external/sensitive action is still manual.

### Next automation roadmap
- **P22**: explicit approval decision endpoints and gate nodes.
- **P23**: memory/persistence manager.
- **P24**: evaluator agent and quality metrics harness.

---

## D) Why `/p21/langgraph/run` may return 404

Usually this means your local code is behind and does not include that route yet.

Run:

```bash
git fetch origin --prune
git checkout phase3-dev
git pull --rebase origin phase3-dev
```

Then restart API process and re-run curl.

