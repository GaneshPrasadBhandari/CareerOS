import streamlit as st
import httpx

st.set_page_config(page_title="CareerOS", layout="wide")
st.title("CareerOS — Capstone MVP")
st.caption("Resume + Jobs → Rank → Grounded Artifacts → Guardrails → Export")

api_url = st.text_input("API URL", value="http://127.0.0.1:8000")

if st.button("Check API Health", key="btn_health"):
    try:
        r = httpx.get(f"{api_url}/health", timeout=5)
        st.success("API reachable")
        st.json(r.json())
    except Exception as e:
        st.error(f"API not reachable: {e}")

if st.button("Check API Version", key="btn_version"):
    try:
        r = httpx.get(f"{api_url}/version", timeout=5)
        st.json(r.json())
    except Exception as e:
        st.error(f"API not reachable: {e}")



#Add Streamlit section L1
st.subheader("L1 Intake (Create Intake Bundle)")

name = st.text_input("Candidate name (optional)")
roles = st.text_input("Target roles (comma-separated)", value="GenAI Solution Architect, ML Engineer")
location = st.text_input("Preferred location", value="USA")
remote_only = st.checkbox("Remote only", value=True)
salary_min = st.number_input("Salary min", min_value=0, value=120000, step=5000)
salary_max = st.number_input("Salary max", min_value=0, value=180000, step=5000)
work_auth = st.text_input("Work authorization (optional)", value="F1 CPT (Jan-May 2026), OPT after May 2026")

if st.button("Create Intake Bundle", key="btn_intake"):
    payload = {
        "version": "v1",
        "candidate_name": name or None,
        "target_roles": [r.strip() for r in roles.split(",") if r.strip()],
        "target_industries": [],
        "constraints": {
            "location": location or None,
            "remote_only": remote_only,
            "salary_min": int(salary_min) if salary_min else None,
            "salary_max": int(salary_max) if salary_max else None,
            "work_auth": work_auth or None,
            "relocation_ok": False,
        },
        "links": {"linkedin_url": None, "github_url": None, "portfolio_url": None},
        "notes": None,
    }

    try:
        r = httpx.post(f"{api_url}/intake", json=payload, timeout=10)
        st.json(r.json())
    except Exception as e:
        st.error(f"Failed to create intake bundle: {e}")


#Add Streamlit section L2
st.subheader("L2 Parsing (Resume Text → Evidence Profile)")

candidate = st.text_input("Candidate name", value="")
resume_text = st.text_area("Paste resume text here", height=200)

if st.button("Build Profile", key="btn_profile"):
    payload = {"candidate_name": candidate or None, "resume_text": resume_text}
    try:
        r = httpx.post(f"{api_url}/profile", json=payload, timeout=20)
        st.json(r.json())
    except Exception as e:
        st.error(f"Failed to build profile: {e}")


#Add Streamlit section L3
st.subheader("L3 Jobs (Paste Job Description → JobPost Artifact)")

job_url = st.text_input("Job URL (optional)", value="", key="job_url")
job_text = st.text_area("Paste job description here", height=200, key="job_text")

if st.button("Ingest Job Post", key="btn_job_ingest"):
    payload = {"url": job_url or None, "job_text": job_text}
    try:
        r = httpx.post(f"{api_url}/jobs/ingest", json=payload, timeout=20)
        st.json(r.json())
    except Exception as e:
        st.error(f"Failed to ingest job: {e}")




#Add Streamlit section L4
st.subheader("L4 Matching (EvidenceProfile + JobPost → MatchResult)")

if st.button("Run Matching (latest profile + latest job)", key="btn_match"):
    try:
        r = httpx.post(f"{api_url}/match/run", timeout=30)
        st.json(r.json())
    except Exception as e:
        st.error(f"Failed to run matching: {e}")


#add Streamlit L5 section
st.subheader("L5 Ranking (All Jobs → Ranked Shortlist)")

top_n = st.number_input("Top N", min_value=1, max_value=10, value=3, step=1)

if st.button("Run Ranking (latest profile + all jobs)", key="btn_rank"):
    try:
        r = httpx.post(f"{api_url}/rank/run", params={"top_n": int(top_n)}, timeout=60)
        st.json(r.json())
    except Exception as e:
        st.error(f"Failed to run ranking: {e}")


#Add Streamlit P6 section
st.subheader("P6 Generation (Top Job → Application Package)")

if st.button("Generate Application Package (Top-1 job)", key="btn_generate_pkg"):
    try:
        r = httpx.post(f"{api_url}/generate/package", timeout=60)
        st.json(r.json())
    except Exception as e:
        st.error(f"Failed to generate package: {e}")
