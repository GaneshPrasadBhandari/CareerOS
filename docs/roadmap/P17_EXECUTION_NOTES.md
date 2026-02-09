# P17 Execution Notes — Grounded Generation v2
+
+## AI architecture alignment

### P16 alignment
**Layer 4 (AI/ML decisioning):** hybrid match score combines semantic signals and constraints.
**Layer 7 (analytics/learning):** scoring weights and outcomes are inspectable for later tuning.
**Layer 8 (memory/models):** retrieval and embeddings provide semantic evidence support.
**Layer 9 (governance/ops):** match rationale and evidence coverage are logged for explainability.

### P17 alignment
**Layer 4 (generation logic):** generated bullets and package content are formed from retrieved evidence.
**Layer 8 (memory/models):** evidence chunks are the grounding source (citation ids attached to output).
**Layer 9 (governance/ops):** citation-required contract is explicit (`citations_required`, `citations_complete`).

## What / How / Why for P17

**What:** Add evidence chunk schema and retrieval utility.
**How:** Introduced `EvidenceChunk` and `EvidenceRetrievalResult` plus profile-skill chunk retrieval.
**Why:** P17 requires generation to be grounded on explicit chunk references, not only skill names.

**What:** Extend generation schema for citation pointers.
**How:** Added `evidence_chunk_ids` to each bullet and introduced `ApplicationPackageV2` contract.
**Why:** Enforces traceability at bullet level and establishes v2 package compatibility for P17.
+
**What:** Build grounded package generation service.
**How:** Added v2 builders that map overlap skills → chunk ids and mark citation completeness.
**Why:** Makes grounding machine-checkable before export/approval flows.

**What:** Add regression test for P17 behavior.
**How:** Unit test validates v2 package includes chunk citations for all generated bullets.
**Why:** Prevents regressions where generation forgets to attach evidence pointers.
