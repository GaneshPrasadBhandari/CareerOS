import streamlit as st
import httpx
import requests
import pandas as pd
import sys
import os
from pathlib import Path

# 1. SETUP DIRECTORIES
ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# 2. CONFIGURE PAGE
st.set_page_config(page_title="CareerOS", layout="wide")
st.title("CareerOS — Capstone MVP")
st.caption("Resume + Jobs → Rank → Grounded Artifacts → Guardrails → Export")

# 3. DYNAMIC API ROUTING (The Fix)
# We look for the Streamlit Secret first. If it doesn't exist, we fall back to local.
cloud_secret_url = st.secrets.get("API_URL", "http://127.0.0.1:8000")

# Use session state to ensure the URL persists during the session
if "api_url" not in st.session_state:
    st.session_state["api_url"] = cloud_secret_url

# This text input will now default to your Render URL in the cloud!
api_url = st.text_input(
    "API URL", 
    value=st.session_state["api_url"], 
    help="Automatically set via Streamlit Secrets in production."
)
st.session_state["api_url"] = api_url

# 4. LIVE CONNECTIVITY CHECK
try:
    # We check /health to confirm the backend is awake
    _health = httpx.get(f"{api_url}/health", timeout=5)
    if _health.status_code == 200:
        st.success(f"✅ Connected to Backend: {api_url}")
    else:
        st.warning(f"⚠️ Backend found but returned status {_health.status_code}")
except Exception as _e:
    st.error(
        f"❌ API not reachable at {api_url}. \n\n"
        "If you are on Render, open your backend URL in a new tab to wake it up: "
        "https://careeros-backend-d9sc.onrender.com"
    )

# --- START OF APP SECTIONS ---

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

with st.expander("Pipeline Progress (P1-P19)", expanded=False):
    if st.button("Refresh P1-P19 Status", key="btn_phases_refresh"):
        try:
            r = httpx.get(f"{api_url}/phases/status", timeout=10)
            st.json(r.json())
        except Exception as e:
            st.error(f"Failed to load phases: {e}")

if st.button("Check Phase Coverage (P1-P19)", key="btn_phases"):
    try:
        r = httpx.get(f"{api_url}/phases/status", timeout=10)
        data = r.json()
        st.json(data)
    except Exception as e:
        st.error(f"Failed to load phases: {e}")

# L1 Intake
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
            "salary_min": int(salary_min),
            "salary_max": int(salary_max),
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

# L2 Parsing
st.subheader("L2 Parsing (Resume Text → Evidence Profile)")
candidate = st.text_input("Candidate name", value="", key="l2_cand_name")
resume_text = st.text_area("Paste resume text here", height=200)

if st.button("Build Profile", key="btn_profile"):
    payload = {"candidate_name": candidate or None, "resume_text": resume_text}
    try:
        r = httpx.post(f"{api_url}/profile", json=payload, timeout=20)
        st.json(r.json())
    except Exception as e:
        st.error(f"Failed to build profile: {e}")

# L3 Jobs
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

# L4 Matching
st.subheader("L4 Matching (EvidenceProfile + JobPost → MatchResult)")
if st.button("Run Matching (latest profile + latest job)", key="btn_match"):
    try:
        r = httpx.post(f"{api_url}/match/run", timeout=30)
        st.json(r.json())
    except Exception as e:
        st.error(f"Failed to run matching: {e}")

# L5 Ranking
st.subheader("L5 Ranking (All Jobs → Ranked Shortlist)")
top_n = st.number_input("Top N", min_value=1, max_value=10, value=3, step=1)
if st.button("Run Ranking (latest profile + all jobs)", key="btn_rank"):
    try:
        r = httpx.post(f"{api_url}/rank/run", params={"top_n": int(top_n)}, timeout=60)
        st.json(r.json())
    except Exception as e:
        st.error(f"Failed to run ranking: {e}")

# P6 Generation
st.subheader("P6 Generation (Top Job → Application Package)")
if st.button("Generate Application Package (Top-1 job)", key="btn_generate_pkg"):
    try:
        r = httpx.post(f"{api_url}/generate/package", timeout=60)
        st.json(r.json())
    except Exception as e:
        st.error(f"Failed to generate package: {e}")

# P7 Guardrails
st.subheader("P7 Guardrails (Validate Application Package)")
if st.button("Validate Latest Package", key="btn_guardrails"):
    try:
        r = httpx.post(f"{api_url}/guardrails/validate", timeout=60)
        st.json(r.json())
    except Exception as e:
        st.error(f"Guardrails validation failed: {e}")

# P8 Export
st.header("P8 — Export + Apply Tracking")
with st.expander("Export Latest Validated Package (DOCX + PDF)", expanded=True):
    col1, col2 = st.columns(2)
    export_docx = col1.checkbox("Export DOCX", value=True)
    export_pdf = col2.checkbox("Export PDF", value=True)
    out_dir = st.text_input("Output folder", value="exports/submissions")
    if st.button("Export Latest Approved Package"):
        payload = {"export_docx": export_docx, "export_pdf": export_pdf, "out_dir": out_dir}
        resp = requests.post(f"{api_url}/export/package", json=payload, timeout=60)
        if resp.status_code == 200:
            st.success("Export created")
            st.json(resp.json())
        else:
            st.error(f"Export failed ({resp.status_code})")

# P25 ONE-CLICK
st.header("P25 — One-Click Automation (Upload Resume + Job File)")
p25_candidate = st.text_input("P25 Candidate Name", value="Demo Candidate", key="p25_name")
p25_top_n = st.number_input("P25 Top N", min_value=1, max_value=10, value=3, step=1, key="p25_n")
resume_upload = st.file_uploader("Upload resume file", type=["txt", "pdf", "docx"], key="p25_res")
job_upload = st.file_uploader("Upload job description", type=["txt", "pdf", "docx"], key="p25_job")

if st.button("Run P25 Automation"):
    if not resume_upload or not job_upload:
        st.warning("Please upload both files.")
    else:
        try:
            files = {
                "resume_file": (resume_upload.name, resume_upload.getvalue(), resume_upload.type),
                "job_file": (job_upload.name, job_upload.getvalue(), job_upload.type),
            }
            data = {"candidate_name": p25_candidate, "top_n": int(p25_top_n)}
            r = requests.post(f"{api_url}/p25/automation/run_upload", files=files, data=data, timeout=120)
            st.success("P25 automation completed")
            st.json(r.json())
        except Exception as e:
            st.error(f"P25 run failed: {e}")