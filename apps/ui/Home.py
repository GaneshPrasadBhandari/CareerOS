import streamlit as st
import httpx
import requests
import pandas as pd
import sys
from pathlib import Path
from urllib.parse import quote

# 1. SETUP DIRECTORIES
ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Variables for local state
resume_text = ""
job_desc = ""

# 2. CONFIGURE PAGE
st.set_page_config(page_title="CareerOS", layout="wide")
st.title("CareerOS — Capstone MVP")
st.caption("Resume + Jobs → Rank → Grounded Artifacts → Guardrails → Export")

# 3. DYNAMIC API ROUTING (Cloud-First Fix)
# This looks for the secret you added in the Streamlit Dashboard.
cloud_api_url = st.secrets.get("API_URL") or st.secrets.get("BACKEND_URL") or "https://careeros-backend-d9sc.onrender.com"

if "api_url" not in st.session_state:
    st.session_state["api_url"] = cloud_api_url

api_url = st.text_input(
    "API URL", 
    value=st.session_state["api_url"], 
    help="Automatically pulls from Streamlit Secrets if deployed."
)
st.session_state["api_url"] = api_url

# 4. LIVE CONNECTIVITY CHECK
try:
    _health = httpx.get(f"{api_url}/health", timeout=5)
    if _health.status_code == 200:
        st.success(f"✅ API connected: {api_url}")
    else:
        st.warning(f"⚠️ API responded with status={_health.status_code}. URL: {api_url}")
except Exception as _e:
    st.error(
        f"❌ API not reachable at {api_url}. \n\n"
        "If you are on Render, wake it up by opening your backend URL in a new tab: "
        "https://careeros-backend-d9sc.onrender.com"
    )

# --- SYSTEM UTILS ---

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

# --- CORE PIPELINE SECTIONS ---

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
        "constraints": {
            "location": location or None,
            "remote_only": remote_only,
            "salary_min": int(salary_min),
            "salary_max": int(salary_max),
            "work_auth": work_auth or None,
            "relocation_ok": False,
        }
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

# L4/L5 Matching & Ranking
st.subheader("L4/L5 Matching & Ranking")
top_n = st.number_input("Top N Jobs to Rank", min_value=1, max_value=10, value=3)

if st.button("Run Match & Rank", key="btn_match_rank"):
    try:
        m = httpx.post(f"{api_url}/match/run", timeout=30)
        r = httpx.post(f"{api_url}/rank/run", params={"top_n": int(top_n)}, timeout=60)
        st.success("Matching and Ranking complete.")
        st.json(r.json())
    except Exception as e:
        st.error(f"Process failed: {e}")

# P25 ONE-CLICK AUTOMATION
st.header("P25 — One-Click Automation (Upload Resume + Job File)")

p25_candidate = st.text_input("P25 Candidate Name", value="Demo Candidate")
p25_top_n = st.number_input("P25 Top N", min_value=1, max_value=10, value=3, step=1, key="p25_n_input")
resume_upload = st.file_uploader("Upload resume file", type=["txt", "pdf", "docx"], key="p25_resume_upload")
job_upload = st.file_uploader("Upload job description", type=["txt", "pdf", "docx"], key="p25_job_upload")

if st.button("Run P25 Automation from Uploaded Files"):
    if not resume_upload or not job_upload:
        st.warning("Please upload both resume and job files.")
    else:
        try:
            files = {
                "resume_file": (resume_upload.name, resume_upload.getvalue(), resume_upload.type or "application/octet-stream"),
                "job_file": (job_upload.name, job_upload.getvalue(), job_upload.type or "application/octet-stream"),
            }
            data = {"candidate_name": p25_candidate, "top_n": int(p25_top_n)}
            r = requests.post(f"{api_url}/p25/automation/run_upload", files=files, data=data, timeout=120)
            if r.status_code == 200:
                st.success("P25 automation completed successfully!")
                payload = r.json()
                st.json(payload)
                llm = payload.get("llm_summary", {})
                if llm:
                    st.info(f"LLM provider: {llm.get('provider', 'n/a')} | tier: {llm.get('tier', 'n/a')} | status: {llm.get('status', 'n/a')}")
                paths = payload.get("paths", {})
                if paths:
                    st.markdown("### Open generated artifacts")
                    for label, pth in paths.items():
                        if pth:
                            encoded = quote(str(pth), safe="")
                            st.markdown(f"- **{label}**: [open]({api_url}/artifacts/open?path={encoded}) | [read]({api_url}/artifacts/read?path={encoded})")
            else:
                st.error(f"P25 run failed ({r.status_code})")
                st.write(r.text)
        except Exception as e:
            st.error(f"P25 run failed: {e}")



st.header("P25 — Daily Top-20 Job Discovery + Tailored Pack")
st.caption("Auto-discover jobs from top sources for selected roles, rank top jobs, generate tailored resume+cover letter, and surface HITL confidence.")

auto_role_choices = st.multiselect(
    "Select 3-5 target roles",
    [
        "ML Engineer", "Data Scientist", "Backend Engineer", "GenAI Engineer",
        "Software Engineer", "AI Engineer", "MLOps Engineer", "Data Engineer",
    ],
    default=["ML Engineer", "Backend Engineer", "GenAI Engineer"],
)
auto_location = st.text_input("Target location for discovery", value="USA", key="auto_location")
auto_daily_limit = st.number_input("Daily job cap", min_value=5, max_value=50, value=20, key="auto_daily_limit")
auto_top_n = st.number_input("Top jobs to rank for tailored output", min_value=1, max_value=20, value=5, key="auto_top_n")
auto_private_mode = st.checkbox("Private mode (PII redaction in persisted artifacts)", value=True, key="auto_private_mode")
auto_resume_source_type = st.selectbox("Resume source type", ["inline", "linkedin_url", "website"], index=0, key="auto_resume_source")
auto_resume_input = st.text_area("Resume text or LinkedIn/website URL", height=140, key="auto_resume_input")
auto_resume_upload = st.file_uploader("Or upload resume (pdf/docx/txt)", type=["txt", "pdf", "docx"], key="auto_resume_upload")

if st.button("Run Daily Auto-Discovery + Tailored Generation", key="btn_p25_daily"):
    if not auto_resume_input.strip() and not auto_resume_upload:
        st.warning("Please provide resume text or URL.")
    else:
        try:
            if auto_resume_upload is not None:
                files = {
                    "resume_file": (
                        auto_resume_upload.name,
                        auto_resume_upload.getvalue(),
                        auto_resume_upload.type or "application/octet-stream",
                    )
                }
                data = {
                    "candidate_name": p25_candidate,
                    "top_n": int(auto_top_n),
                    "roles_csv": ",".join(auto_role_choices),
                    "location": auto_location,
                    "daily_limit": int(auto_daily_limit),
                    "private_mode": str(bool(auto_private_mode)).lower(),
                }
                r = requests.post(f"{api_url}/p25/automation/run_upload_auto", files=files, data=data, timeout=240)
            else:
                resume_payload = {"source_type": auto_resume_source_type}
                if auto_resume_source_type == "inline":
                    resume_payload["text"] = auto_resume_input.strip()
                else:
                    resume_payload["source_url"] = auto_resume_input.strip()

                payload = {
                    "candidate_name": p25_candidate or None,
                    "top_n": int(auto_top_n),
                    "privacy": {"private_mode": bool(auto_private_mode)},
                    "resume": resume_payload,
                    "jobs": {
                        "auto_discover": True,
                        "daily_limit": int(auto_daily_limit),
                        "max_per_source": 2,
                        "preferences": {
                            "roles": auto_role_choices,
                            "location": auto_location,
                        },
                    },
                }
                r = httpx.post(f"{api_url}/p25/automation/run", json=payload, timeout=240)
            st.json(r.json())
            if r.status_code == 200:
                body = r.json()
                hitl = body.get("hitl", {})
                if hitl:
                    conf = hitl.get("confidence_percent", 0)
                    st.progress(min(100, int(conf)))
                    if hitl.get("approval_required"):
                        st.warning(f"HITL approval required | Confidence: {conf}%")
                    else:
                        st.success(f"HITL check passed | Confidence: {conf}%")
                    st.write("Reasons:")
                    for reason in hitl.get("reasons", []):
                        st.write(f"- {reason}")
        except Exception as e:
            st.error(f"Daily automation failed: {e}")


if st.button("Run P1→P25 Quick Pipeline (One Click)", key="btn_p1_p25_quick"):
    if not auto_resume_input.strip() and not auto_resume_upload:
        st.warning("Please provide resume text/URL or upload resume first.")
    else:
        try:
            intake_payload = {
                "version": "v1",
                "candidate_name": p25_candidate or None,
                "target_roles": auto_role_choices,
                "constraints": {
                    "location": auto_location,
                    "remote_only": True,
                    "salary_min": 100000,
                    "salary_max": 250000,
                    "work_auth": None,
                    "relocation_ok": False,
                },
            }
            intake_resp = httpx.post(f"{api_url}/intake", json=intake_payload, timeout=30)
            st.write("P1 intake:", intake_resp.json())
            st.write("Running P25 automation...")
            st.info("Use 'Run Daily Auto-Discovery + Tailored Generation' result above for full P25 artifact outputs.")
        except Exception as e:
            st.error(f"Quick pipeline failed: {e}")

if st.button("Check Storage/DB/Vector Status", key="btn_storage_status"):
    try:
        r = httpx.get(f"{api_url}/system/storage/status", timeout=20)
        st.json(r.json())
    except Exception as e:
        st.error(f"Failed to load storage status: {e}")


st.header("Artifact Viewer")
artifact_path = st.text_input("Artifact path (outputs/... or exports/...)", value="")
if st.button("Open Artifact", key="btn_open_artifact") and artifact_path.strip():
    encoded = quote(artifact_path.strip(), safe="")
    st.markdown(f"[Open file]({api_url}/artifacts/open?path={encoded})")
    try:
        rr = httpx.get(f"{api_url}/artifacts/read", params={"path": artifact_path.strip()}, timeout=20)
        st.json(rr.json())
    except Exception as e:
        st.error(f"Failed to read artifact: {e}")

st.header("Feedback (User Testing)")
fb_user_id = st.text_input("User ID", value="")
fb_email = st.text_input("Email", value="")
fb_run_id = st.text_input("Run ID", value="")
fb_rating = st.slider("Rating", min_value=1, max_value=5, value=4)
fb_category = st.selectbox("Feedback category", ["general", "ranking", "generation", "jobs", "ui", "bug"]) 
fb_message = st.text_area("Feedback message", height=120)

if st.button("Submit Feedback", key="btn_submit_feedback"):
    payload = {
        "user_id": fb_user_id or None,
        "email": fb_email or None,
        "run_id": fb_run_id or None,
        "rating": int(fb_rating),
        "category": fb_category,
        "message": fb_message,
    }
    try:
        r = httpx.post(f"{api_url}/feedback/submit", json=payload, timeout=20)
        st.success("Feedback submitted")
        st.json(r.json())
    except Exception as e:
        st.error(f"Failed to submit feedback: {e}")

if st.button("Load Recent Feedback", key="btn_feedback_list"):
    try:
        r = httpx.get(f"{api_url}/feedback/list", params={"limit": 25}, timeout=20)
        st.json(r.json())
    except Exception as e:
        st.error(f"Failed to load feedback: {e}")
