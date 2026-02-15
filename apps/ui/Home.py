import sys
import os

# This line tells Python that the 'src' folder contains our packages
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
import httpx
import requests
import pandas as pd
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
# Add this near the top of Home.py
resume_text = ""
job_desc = ""



st.set_page_config(page_title="CareerOS", layout="wide")
st.title("CareerOS — Capstone MVP")
st.caption("Resume + Jobs → Rank → Grounded Artifacts → Guardrails → Export")

default_api = st.session_state.get("api_url", "http://127.0.0.1:8000")
api_url = st.text_input("API URL", value=default_api, help="Run API first: scripts/run_phase2_app.sh api")
st.session_state["api_url"] = api_url

# live connectivity hint (prevents confusing Connection refused errors across sections)
try:
    _health = httpx.get(f"{api_url}/health", timeout=2)
    if _health.status_code == 200:
        st.success(f"API connected: {api_url}")
    else:
        st.warning(f"API responded with status={_health.status_code}. URL: {api_url}")
except Exception as _e:
    st.error(
        "API not reachable. Start FastAPI first in terminal: `scripts/run_phase2_app.sh api` "
        f"(current URL: {api_url}, error: {_e})"
    )

if st.button("Check API Health", key="btn_health"):
    try:
        r = httpx.get(f"{api_url}/health", timeout=5)
        st.success("API reachable")
        st.json(r.json())
    except Exception as e:
        st.error(f"API not reachable: {e}. Start API: scripts/run_phase2_app.sh api")

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
            st.error(f"Failed to load phases: {e}. Ensure API is running: scripts/run_phase2_app.sh api")


if st.button("Check Phase Coverage (P1-P19)", key="btn_phases"):
    try:
        r = httpx.get(f"{api_url}/phases/status", timeout=10)
        data = r.json()
        st.json(data)
    except Exception as e:
        st.error(f"Failed to load phases: {e}. Ensure API is running: scripts/run_phase2_app.sh api")



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
        st.error(f"Failed to create intake bundle: {e}. Ensure API is running: scripts/run_phase2_app.sh api")


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
# add section for p10
st.header("P10 — Next Actions (Follow-up Scheduler)")

col1, col2 = st.columns(2)
with col1:
    followup_days = st.number_input(
    "Follow-up after idle days",
    min_value=1,
    max_value=14,
    value=3,
    key="p10_followup_days",
)
with col2:
    stale_days = st.number_input(
    "Stale application days",
    min_value=7,
    max_value=60,
    value=14,
    key="p10_stale_days",
)

def _render_queue(q: dict):
    st.subheader("Action Queue")
    st.write(f"Generated at: {q.get('created_at_utc')} | Total: {q.get('total')}")
    actions = q.get("actions", [])
    if actions:
        import pandas as pd
        st.dataframe(pd.DataFrame(actions), use_container_width=True)
    else:
        st.info("No actions generated.")

if st.button("Generate Next Actions"):
    resp = requests.post(
        f"{api_url}/followups/generate",
        params={"followup_days": int(followup_days), "stale_days": int(stale_days)},
        timeout=30,
    )
    if resp.status_code == 200:
        st.success("Generated follow-up actions")
        data = resp.json()
        st.json(data)

        # Prefer queue if present, otherwise fall back to latest
        q = data.get("queue")
        if not q:
            latest = requests.get(f"{api_url}/followups/latest", timeout=30).json()
            q = (latest or {}).get("queue")
        if q:
            _render_queue(q)
    else:
        st.error(resp.text)

if st.button("Load Latest Actions"):
    resp = requests.get(f"{api_url}/followups/latest", timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        q = data.get("queue", {})
        if q:
            _render_queue(q)
        else:
            st.info("No latest actions found. Generate actions first.")
            st.json(data)
    else:
        st.error(resp.text)


#add section for p11
st.header("P11 — Draft Messages (Notifications)")

def _render_drafts(bundle: dict):
    st.subheader("Draft Bundle")
    st.write(f"Generated at: {bundle.get('created_at_utc')} | Total: {bundle.get('total')}")
    items = bundle.get("items", [])
    if not items:
        st.info("No drafts generated.")
        return

    import pandas as pd
    # Flatten for table
    rows = []
    for it in items:
        for m in it.get("messages", []):
            rows.append({
                "application_id": it.get("application_id"),
                "action_type": it.get("action_type"),
                "priority": it.get("priority"),
                "channel": m.get("channel"),
                "subject": m.get("subject"),
                "body": m.get("body"),
                "due_at_utc": it.get("due_at_utc"),
            })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

if st.button("Generate Drafts"):
    resp = requests.post(f"{api_url}/notifications/generate", timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        st.success("Generated drafts")
        b = (data or {}).get("bundle")
        if b:
            _render_drafts(b)
        else:
            st.json(data)
    else:
        st.error(resp.text)

if st.button("Load Latest Drafts"):
    resp = requests.get(f"{api_url}/notifications/latest", timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        b = (data or {}).get("bundle")
        if b:
            st.success("Loaded latest drafts")
            _render_drafts(b)
        else:
            st.json(data)
    else:
        st.error(resp.text)



#add section for p12 orchestrator
st.header("P12 — One-Click Orchestration (P6→P11)")

profile_path = st.text_input("profile_path (latest or choose)", value="")
job_path = st.text_input("job_path (latest or choose)", value="")
overlap_skills_txt = st.text_input("overlap_skills (comma-separated)", value="python,docker")

followup_days = st.number_input(
    "Follow-up after idle days",
    min_value=1,
    max_value=14,
    value=3,
    key="p12_followup_days",
)

stale_days = st.number_input(
    "Stale application days",
    min_value=7,
    max_value=60,
    value=14,
    key="p12_stale_days",
)

if st.button("Run Orchestrator"):
    payload = {
        "profile_path": profile_path.strip() or None,
        "job_path": job_path.strip() or None,
        "overlap_skills": [s.strip() for s in overlap_skills_txt.split(",") if s.strip()],
    }

    resp = requests.post(
        f"{api_url}/orchestrator/run",
        params={"followup_days": int(followup_days), "stale_days": int(stale_days)},
        json=payload,
        timeout=60,
    )

    if resp.status_code == 200:
        st.success("Orchestrator ran")
        st.json(resp.json())
    else:
        st.error(resp.text)



# --- P15 Human Approval Gate (L5) ---
st.header("P15 — Human Approval Gate (L5)")

# 1. Fetch the pending state from the backend
col_p15_a, col_p15_b, col_p15_c = st.columns(3)
if col_p15_a.button("Check for Pending Approvals"):
    try:
        r = httpx.get(f"{api_url}/orchestrator/current_state", timeout=10)
        if r.status_code == 200:
            state_data = r.json()
            if state_data.get("status") == "idle":
                st.info(state_data.get("message"))
                if 'current_state' in st.session_state:
                    del st.session_state['current_state']
            else:
                st.session_state['current_state'] = state_data
                st.success("Pending match found!")
        else:
            st.error(f"Error: Received status code {r.status_code}")
    except Exception as e:
        st.error(f"Error fetching state: {e}")

if col_p15_b.button("Refresh from Latest Match"):
    try:
        r = httpx.get(f"{api_url}/orchestrator/current_state", params={"refresh": True}, timeout=10)
        if r.status_code == 200:
            st.session_state['current_state'] = r.json()
            st.success("State refreshed from latest match artifact.")
            st.json(r.json())
        else:
            st.error(r.text)
    except Exception as e:
        st.error(f"Refresh failed: {e}")

if col_p15_c.button("Reset Approval State"):
    try:
        r = httpx.post(f"{api_url}/orchestrator/reset", timeout=10)
        if r.status_code == 200:
            st.session_state.pop('current_state', None)
            st.success("State reset. Run matching/ranking again if needed.")
        else:
            st.error(r.text)
    except Exception as e:
        st.error(f"Reset failed: {e}")


# 2. Display UI if a valid state is stored in session_state
if 'current_state' in st.session_state:
    cs = st.session_state['current_state']
    
    with st.container(border=True):
        st.subheader(f"Review Match: {cs.get('top_match_id', 'Unknown ID')}")
        
        # Format the score as a percentage for readability
        score_raw = cs.get('match_score', 0)
        try:
            score_val = float(score_raw)
        except Exception:
            score_val = 0.0
        score_pct = score_val if score_val > 1.0 else score_val * 100.0
        st.metric("AI Match Score", f"{score_pct:.1f}%")
        st.caption(f"Overlap skills: {', '.join(cs.get('overlap_skills', [])[:10]) or 'n/a'}")
        
        feedback = st.text_area(
            "Feedback for Creator Agent", 
            placeholder="E.g., Emphasize my AWS experience more.",
            key="approval_feedback"
        )
        
        col_app, col_rej = st.columns(2)
        
        # Approve Logic
        if col_app.button("✅ Approve Match", type="primary", use_container_width=True):
            # Backend logic only requires the feedback dictionary
            payload = {"user_feedback": feedback}
            try:
                resp = httpx.post(f"{api_url}/orchestrator/approve", json=payload, timeout=10)
                if resp.status_code == 200:
                    st.success("Match Approved! You can now run P6 Generation.")
                    # Refresh local state to reflect approval if desired
                    del st.session_state['current_state']
                else:
                    st.error(f"Approval failed: {resp.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")
            
        # Reject Logic
        if col_rej.button("❌ Reject & Re-Run Match/Rank", use_container_width=True):
            try:
                resp = httpx.post(f"{api_url}/orchestrator/reject", json={"feedback": feedback}, timeout=10)
                if resp.status_code == 200:
                    st.warning("Match rejected. Re-running P4/P5 on latest artifacts...")
                    m = httpx.post(f"{api_url}/match/run", timeout=30)
                    r = httpx.post(f"{api_url}/rank/run", params={"top_n": 3}, timeout=30)
                    st.session_state.pop('current_state', None)
                    if m.status_code == 200 and r.status_code == 200:
                        st.success("Re-run complete. Click 'Refresh from Latest Match' to review updated state.")
                    else:
                        st.error(f"Re-run issues: match={m.status_code}, rank={r.status_code}")
                else:
                    st.error(f"Reject failed: {resp.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")



# --- P17 GROUNDED EVIDENCE SECTION ---
st.header("P17 — Grounded Evidence Analysis")
st.caption("You can either reuse P2/P3 text or paste dedicated inputs below.")

p17_resume_text = st.text_area("P17 Resume Text (optional override)", value="", height=140)
p17_job_text = st.text_area("P17 Job Description Text (optional override)", value="", height=140)

if st.button("Run P17 Grounding Analysis"):
    resume_input = p17_resume_text.strip() or resume_text.strip()
    job_input = p17_job_text.strip() or job_text.strip()

    if not resume_input or not job_input:
        st.error("Please provide resume and job description text (either in P2/P3 or in the P17 override boxes).")
    else:
        payload = {"resume_text": resume_input, "job_text": job_input, "candidate_name": candidate or None}
        try:
            resp = requests.post(f"{api_url}/p17/grounding", json=payload, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                st.success("P17 grounded package generated")
                st.json(
                    {
                        "path": data.get("path"),
                        "required_skills": data.get("required_skills", []),
                        "chunks": len(data.get("retrieved_chunks", [])),
                        "citations_complete": (data.get("package") or {}).get("citations_complete"),
                    }
                )
            else:
                st.error(resp.text)
        except Exception as e:
            st.error(f"P17 request failed: {e}")


# --- P18 GUARDRIALS V2 SECTION ---
st.header("P18 — Guardrails v2 (Citation Enforcement)")

p18_package_path = st.text_input("P18 package_path (optional, auto latest v2)", value="")
if st.button("Run P18 Guardrails v2"):
    try:
        resp = requests.post(f"{api_url}/p18/guardrails_v2", json={"package_path": p18_package_path.strip() or None}, timeout=30)
        if resp.status_code == 200:
            st.json(resp.json())
        else:
            st.error(resp.text)
    except Exception as e:
        st.error(f"P18 request failed: {e}")


# --- P19 GLOBAL STATE SECTION ---
st.header("P19 — Typed Global State (Agentic Prep)")

p19_mode = st.selectbox("P19 mode", ["agentic", "deterministic"], index=0)
if st.button("Create New P19 State"):
    try:
        resp = requests.post(f"{api_url}/p19/state/new", json={"mode": p19_mode}, timeout=20)
        st.json(resp.json())
    except Exception as e:
        st.error(f"P19 create failed: {e}")

if st.button("Load Latest P19 State"):
    try:
        resp = requests.get(f"{api_url}/p19/state/latest", timeout=20)
        st.json(resp.json())
    except Exception as e:
        st.error(f"P19 load failed: {e}")


# --- PHASE 3 KICKOFF ---
st.header("Phase 3 Kickoff — Agentic + LLM Bootstrap")

if st.button("Check Phase 3 Readiness"):
    try:
        r = requests.get(f"{api_url}/phase3/readiness", timeout=20)
        st.json(r.json())
    except Exception as e:
        st.error(f"Readiness failed: {e}")

st.subheader("P20 Contract Validation")
p20_payload = st.text_area(
    "P20 payload JSON",
    value='{"run_id":"demo_run","agent":"planner","objective":"Plan matching and generation","constraints":{}}',
    height=120,
)
if st.button("Run P20 Contract Validate"):
    try:
        import json as _json
        payload = _json.loads(p20_payload)
        r = requests.post(f"{api_url}/p20/contracts/validate", json=payload, timeout=20)
        st.json(r.json())
    except Exception as e:
        st.error(f"P20 failed: {e}")

st.subheader("P21 LangGraph Dry Run")
if st.button("Run P21 Dry Run"):
    try:
        import json as _json
        payload = _json.loads(p20_payload)
        r = requests.post(f"{api_url}/p21/langgraph/dry_run", json=payload, timeout=20)
        st.json(r.json())
    except Exception as e:
        st.error(f"P21 failed: {e}")


if st.button("Run P21 Full Graph (Deterministic)"):
    try:
        import json as _json
        payload = _json.loads(p20_payload)
        payload.setdefault("top_n", 3)
        r = requests.post(f"{api_url}/p21/langgraph/run", json=payload, timeout=60)
        st.json(r.json())
    except Exception as e:
        st.error(f"P21 full run failed: {e}")


# --- P25 ONE-CLICK FILE AUTOMATION ---
st.header("P25 — One-Click Automation (Upload Resume + Job File)")

p25_candidate = st.text_input("P25 Candidate Name", value="Demo Candidate")
p25_top_n = st.number_input("P25 Top N", min_value=1, max_value=10, value=3, step=1)
resume_upload = st.file_uploader("Upload resume file (.txt/.pdf/.docx)", type=["txt", "pdf", "docx"], key="p25_resume_upload")
job_upload = st.file_uploader("Upload job description file (.txt/.pdf/.docx)", type=["txt", "pdf", "docx"], key="p25_job_upload")

if st.button("Run P25 Automation from Uploaded Files"):
    if not resume_upload or not job_upload:
        st.warning("Please upload both resume and job files.")
    else:
        try:
            files = {
                "resume_file": (resume_upload.name, resume_upload.getvalue(), resume_upload.type or "application/octet-stream"),
                "job_file": (job_upload.name, job_upload.getvalue(), job_upload.type or "application/octet-stream"),
            }
            data = {
                "candidate_name": p25_candidate,
                "top_n": int(p25_top_n),
            }
            r = requests.post(f"{api_url}/p25/automation/run_upload", files=files, data=data, timeout=120)
            if r.status_code == 200:
                st.success("P25 automation completed")
                st.json(r.json())
            else:
                st.error(f"P25 upload run failed ({r.status_code})")
                st.write(r.text)
        except Exception as e:
            st.error(f"P25 upload run failed: {e}")
