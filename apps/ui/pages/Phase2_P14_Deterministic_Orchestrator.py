import os
import requests
import streamlit as st

api_url = os.getenv("CAREEROS_API_URL", "http://127.0.0.1:8000")

st.title("Phase-2 — P14 Deterministic Orchestrator")

st.write("Runs the fixed plan: P6 → P7 → P8 → P10 → P11 using your P13 state + artifacts.")

run_id = st.text_input("run_id (from P13 /runs/init)", value="")
profile_path = st.text_input("profile_path", value="outputs/profile/profile_v1_latest.json")
job_path = st.text_input("job_path", value="outputs/jobs/job_post_v1_latest.json")
overlap_skills = st.text_input("overlap_skills (comma-separated)", value="python,docker")

col1, col2 = st.columns(2)
with col1:
    followup_days = st.number_input("followup_days", min_value=1, max_value=14, value=3, key="p14_followup_days")
with col2:
    stale_days = st.number_input("stale_days", min_value=7, max_value=60, value=14, key="p14_stale_days")

if st.button("Execute Plan (P6→P11)", type="primary"):
    payload = {
        "run_id": run_id,
        "profile_path": profile_path,
        "job_path": job_path,
        "overlap_skills": [x.strip() for x in overlap_skills.split(",") if x.strip()],
        "followup_days": int(followup_days),
        "stale_days": int(stale_days),
    }
    r = requests.post(f"{api_url}/runs/execute_plan", json=payload, timeout=120)
    if r.status_code == 200:
        st.success("Plan executed")
        st.json(r.json())
    else:
        st.error(r.text)
