import streamlit as st
import httpx
import requests
import pandas as pd


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


#Add Streamlit section P7
st.subheader("P7 Guardrails (Validate Application Package)")

if st.button("Validate Latest Package", key="btn_guardrails"):
    try:
        r = httpx.post(f"{api_url}/guardrails/validate", timeout=60)
        st.json(r.json())
    except Exception as e:
        st.error(f"Guardrails validation failed: {e}")



#Add Streamlit section P8
st.header("P8 — Export + Apply Tracking")

with st.expander("Export Latest Validated Package (DOCX + PDF)", expanded=True):
    col1, col2 = st.columns(2)
    export_docx = col1.checkbox("Export DOCX", value=True)
    export_pdf = col2.checkbox("Export PDF", value=True)

    out_dir = st.text_input("Output folder", value="exports/submissions")

    if st.button("Export Latest Approved Package"):
        payload = {
            "package_path": None,
            "validation_report_path": None,
            "export_docx": export_docx,
            "export_pdf": export_pdf,
            "out_dir": out_dir,
        }
        resp = requests.post(f"{api_url}/export/package", json=payload, timeout=60)
        if resp.status_code == 200:
            st.success("Export created + tracking record appended")
            st.json(resp.json())
        else:
            st.error(f"Export failed ({resp.status_code})")
            st.write(resp.text)

with st.expander("Update Application Status", expanded=False):
    app_id = st.text_input("application_id")
    new_status = st.selectbox(
        "new_status",
        ["draft", "validated", "exported", "submitted", "rejected", "interview", "offer", "withdrawn"],
        index=3,
    )
    if st.button("Update Status"):
        payload = {"application_id": app_id, "new_status": new_status}
        resp = requests.post(f"{api_url}/apply/update_status", json=payload, timeout=30)
        if resp.status_code == 200:
            st.success("Status updated")
            st.json(resp.json())
        else:
            st.error(f"Update failed ({resp.status_code})")
            st.write(resp.text)



#ADD a P9 section
st.header("P9 — Applications Dashboard + Funnel Metrics")

# -----------------------
# Metrics
# -----------------------
st.subheader("Funnel Metrics")

try:
    m = requests.get(f"{api_url}/applications/metrics", timeout=20)
    if m.status_code == 200:
        metrics = m.json()
        st.markdown("**Funnel counts**")
        st.json(metrics.get("funnel", {}))

        st.markdown("**Conversion rates**")
        st.json(metrics.get("conversion", {}))

        st.markdown("**By status**")
        st.json(metrics.get("by_status", {}))
    else:
        st.error(f"Metrics failed ({m.status_code})")
        st.write(m.text)
except Exception as e:
    st.error(f"Metrics request error: {e}")

# -----------------------
# List + filter
# -----------------------
st.subheader("Applications List")

status_filter = st.selectbox(
    "Filter by status",
    [
        "(all)",
        "draft",
        "validated",
        "exported",
        "submitted",
        "interview",
        "offer",
        "rejected",
        "withdrawn",
    ],
    index=0,
)

limit = st.slider("Rows", min_value=10, max_value=200, value=50, step=10)
status_q = None if status_filter == "(all)" else status_filter

try:
    r = requests.get(
        f"{api_url}/applications/list",
        params={"status": status_q, "limit": limit},
        timeout=20,
    )
    if r.status_code == 200:
        data = r.json()
        items = data.get("items", [])
        if items:
            df = pd.DataFrame(items)
            # Nice ordering if present
            cols_pref = [
                "application_id",
                "status",
                "created_at_utc",
                "updated_at_utc",
                "run_id",
                "job_path",
                "package_path",
                "validation_report_path",
                "export_docx_path",
                "export_pdf_path",
            ]
            cols = [c for c in cols_pref if c in df.columns] + [c for c in df.columns if c not in cols_pref]
            df = df[cols]
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No applications found for this filter.")
    else:
        st.error(f"List failed ({r.status_code})")
        st.write(r.text)
except Exception as e:
    st.error(f"List request error: {e}")

# -----------------------
# Drill-down
# -----------------------
st.subheader("Open a specific application record")

app_id = st.text_input("application_id (copy from table above)")

col_a, col_b = st.columns(2)
with col_a:
    if st.button("Fetch Application Record"):
        if not app_id.strip():
            st.warning("Please enter an application_id")
        else:
            try:
                g = requests.get(f"{api_url}/applications/{app_id.strip()}", timeout=20)
                if g.status_code == 200:
                    st.json(g.json())
                else:
                    st.error(f"Fetch failed ({g.status_code})")
                    st.write(g.text)
            except Exception as e:
                st.error(f"Fetch request error: {e}")

with col_b:
    if st.button("Quick-fill latest (copy manually from table)"):
        st.info("Tip: copy an application_id from the table above and paste it here.")


#add section for p10
st.header("P10 — Next Actions (Follow-up Scheduler)")

col1, col2 = st.columns(2)
with col1:
    followup_days = st.number_input("Follow-up after idle days", min_value=1, max_value=14, value=3)
with col2:
    stale_days = st.number_input("Stale application days", min_value=7, max_value=60, value=14)

if st.button("Generate Next Actions"):
    resp = requests.post(
        f"{api_url}/followups/generate",
        params={"followup_days": int(followup_days), "stale_days": int(stale_days)},
        timeout=30,
    )
    if resp.status_code == 200:
        st.success("Generated follow-up actions")
        st.json(resp.json())
    else:
        st.error(resp.text)

if st.button("Load Latest Actions"):
    resp = requests.get(f"{api_url}/followups/latest", timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        st.subheader("Action Queue")
        st.write(f"Generated at: {data.get('generated_at_utc')} | Total: {data.get('total')}")
        items = data.get("items", [])
        if items:
            import pandas as pd
            st.dataframe(pd.DataFrame(items), use_container_width=True)
        else:
            st.info("No actions generated.")
    else:
        st.error(resp.text)
