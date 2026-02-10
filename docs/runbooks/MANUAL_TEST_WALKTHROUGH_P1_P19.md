# CareerOS Manual Test Walkthrough (P1 → P19)

Use this script to validate the full flow in Streamlit with realistic sample inputs.

## Sample Resume Text (paste in P2)
```text
Ganesh Bhandari
AI/ML Engineer with 4+ years building FastAPI microservices, Python data pipelines, and RAG assistants.
Skills: Python, FastAPI, SQL, Docker, Kubernetes, LangChain, LangGraph, MLflow, AWS, Git, pytest, Streamlit.
Experience:
- Built a retrieval-augmented assistant using LangChain + Chroma; improved answer grounding and reduced hallucination risk.
- Developed FastAPI endpoints for matching and ranking pipelines with JSON artifact outputs.
- Deployed services using Docker and Kubernetes; implemented CI checks and pytest-based regression tests.
- Created dashboards in Streamlit and tracked model/pipeline runs with MLflow.
Education: MS in Computer Science.
```

## Sample Job Description (paste in P3)
```text
Role: Senior AI Engineer
Responsibilities:
- Build production APIs using Python and FastAPI.
- Design and deploy RAG workflows using LangChain and vector databases.
- Collaborate on orchestration using LangGraph and approval workflows.
- Maintain quality with testing, observability, and MLOps practices.
Requirements:
Python, FastAPI, SQL, Docker, Kubernetes, LangChain, LangGraph, MLflow, AWS, Git, pytest.
```

## Manual Step-by-step

1. **Health/Version**
   - Click `Check API Health` and `Check API Version`.
   - Expected: `status: ok`.

2. **P1 Intake**
   - Fill basic preferences and click `Create Intake Bundle`.
   - Expected: output path in `outputs/intake/...json`.

3. **P2 Profile**
   - Paste sample resume and click `Build Profile`.
   - Expected: profile artifact + extracted skills list.

4. **P3 Job Ingest**
   - Paste job description and click `Ingest Job Post`.
   - Expected: job artifact + extracted keywords.

5. **P4 Match**
   - Click `Run Matching`.
   - Expected: score and overlap skills returned.

6. **P5 Rank**
   - Click `Run Ranking`.
   - Expected: shortlist artifact with ranked items.

7. **P6/P7/P8**
   - Generate package → validate guardrails → export package.
   - Expected: package json, validation report, doc/pdf export paths.

8. **P9/P10/P11**
   - Metrics list, followups generation, drafts generation.
   - Expected: non-error responses and artifacts.

9. **P12 Orchestrator**
   - Run orchestrator once and inspect response.

10. **P15 Human Gate**
    - Click `Check for Pending Approvals`.
    - If stale, use `Refresh from Latest Match` or `Reset Approval State`.
    - Reject button now re-runs match/rank automatically.

11. **P17 Grounding**
    - Use either P2/P3 text or P17 override text boxes.
    - Click `Run P17 Grounding Analysis`.
    - Expected: path + required_skills + citations_complete.

12. **P18 Guardrails v2**
    - Click `Run P18 Guardrails v2`.
    - Expected: pass/blocked with findings and report path.

13. **P19 State**
    - Click `Create New P19 State` then `Load Latest P19 State`.
    - Expected: typed state JSON and run_id.

## Common confusion clarifications
- P15 `Reject` does **not** ask you to retype resume/job immediately; it re-runs P4/P5 on latest artifacts.
- To change resume/job meaningfully, rerun P2/P3 with new text first.
- P17 does not require comma-separated skills anymore; full text paragraphs are supported.
