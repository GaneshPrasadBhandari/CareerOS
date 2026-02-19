from __future__ import annotations

import io
from urllib.parse import quote

import httpx
import requests
import streamlit as st
import os

st.set_page_config(page_title="CareerOS", layout="wide")
st.title("CareerOS — End-to-End Job Automation Dashboard")
st.caption("L1 Intake → L2 Parse → L3 Discover/Ingest Jobs → L4 Match → L5 Rank → L6 Generate → L7 Guardrails → L8 Summary + Vector DB")


# def _api_url() -> str:
#     cloud_api_url = "https://careeros-backend-d9sc.onrender.com"
#     try:
#         cloud_api_url = st.secrets.get("API_URL") or st.secrets.get("BACKEND_URL") or cloud_api_url
#     except Exception:
#         pass
#     if "api_url" not in st.session_state:
#         st.session_state["api_url"] = cloud_api_url
#     return st.session_state["api_url"]

def _api_url() -> str:
    """
    Determines the Backend API URL based on the environment.
    Priority: Environment Var -> Streamlit Secret -> Localhost
    """
    # 1. Try to get from Environment (Works on Render)
    # 2. Try to get from Streamlit Secrets (Works on Streamlit Cloud)
    # 3. Fallback to Localhost (Works on your MacBook)
    default_url = os.getenv("API_URL") or st.secrets.get("API_URL") or "http://localhost:10000"
    
    if "api_url" not in st.session_state:
        st.session_state["api_url"] = default_url
        
    return st.session_state["api_url"]

# Define the constant globally so you can use it everywhere in the file
API_URL = _api_url()




# --- 1. System Status Logic ---
def check_backend_status():
    """Sidebar indicator for backend connectivity"""
    with st.sidebar:
        st.divider() # Visual separator
        st.subheader("System Status")
        try:
            # Use a short timeout so the UI doesn't hang if the backend is down
            response = requests.get(f"{API_URL}/health", timeout=3)
            if response.status_code == 200:
                st.success("🟢 Backend Online")
                st.caption(f"Endpoint: {API_URL}")
            else:
                st.warning(f"🟠 Backend Issue ({response.status_code})")
        except Exception:
            st.error("🔴 Backend Offline")
            st.info("Ensure the FastAPI server is running.")

# --- 2. Run the check ---
check_backend_status()

# --- 3. Rest of your Home.py content ---
st.title("CareerOS AI Agent")
# ... your resume upload and other features go here







def _extract_pdf_text(raw: bytes) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(raw))
        txt = "\n".join((pg.extract_text() or "") for pg in reader.pages).strip()
        if txt:
            return txt
    except Exception:
        pass

    try:
        import fitz  # pymupdf

        doc = fitz.open(stream=raw, filetype="pdf")
        txt = "\n".join(page.get_text("text") for page in doc).strip()
        if txt:
            return txt
    except Exception:
        pass

    return ""


def _upload_to_text(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    name = (uploaded_file.name or "").lower()
    raw = uploaded_file.getvalue()
    if name.endswith(".pdf"):
        return _extract_pdf_text(raw)
    if name.endswith(".docx"):
        try:
            from docx import Document
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".docx") as tmp:
                tmp.write(raw)
                tmp.flush()
                doc = Document(tmp.name)
                return "\n".join(par.text for par in doc.paragraphs).strip()
        except Exception:
            return raw.decode("utf-8", errors="ignore").strip()
    if name.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff")):
        try:
            import pytesseract
            from PIL import Image

            return pytesseract.image_to_string(Image.open(io.BytesIO(raw))).strip()
        except Exception:
            return ""
    return raw.decode("utf-8", errors="ignore").strip()




def _render_layer_timeline(body: dict) -> None:
    """Render layer-by-layer automation output for run review/evaluation."""
    trace_layers = ((body or {}).get("trace") or {}).get("layers") or {}
    if not trace_layers:
        st.info("No layer trace found in response.")
        return

    order = [
        ("L2_parsing", "Resume Parser"),
        ("L3_jobs", "Job Discovery/Connector"),
        ("L4_matching", "Matcher"),
        ("L5_ranking", "Ranker"),
        ("L6_generation", "Generator"),
        ("L7_guardrails", "Guardrails"),
        ("L8_summary", "LLM Summary"),
    ]

    st.markdown("### Layer-by-layer execution")
    for layer_key, label in order:
        node = trace_layers.get(layer_key)
        if not node:
            continue
        with st.expander(f"{layer_key}: {label}", expanded=False):
            st.write(f"**Agent:** {node.get('agent', 'n/a')}")
            st.write(f"**Next:** {node.get('next_layer', 'n/a')}")
            st.markdown("**Input**")
            st.json(node.get("input", {}))
            st.markdown("**Output**")
            st.json(node.get("output", {}))


def _safe_json(resp: requests.Response | httpx.Response):
    try:
        return resp.json()
    except Exception:
        return {"status": "error", "message": resp.text}


def _queue_l1_sync(name: str, resume_text: str) -> None:
    st.session_state["_pending_sync_name"] = name or ""
    st.session_state["_pending_sync_resume"] = resume_text or ""
    st.session_state["_pending_sync_apply"] = True


if st.session_state.get("_pending_sync_apply"):
    pending_name = str(st.session_state.get("_pending_sync_name") or "")
    pending_resume = str(st.session_state.get("_pending_sync_resume") or "")
    if pending_name:
        st.session_state["l2_name"] = pending_name
        st.session_state["p25_candidate"] = pending_name
    if pending_resume:
        st.session_state["l2_resume"] = pending_resume
        st.session_state["p25_resume_inline"] = pending_resume
    st.session_state["_pending_sync_apply"] = False

with st.sidebar:
    st.header("System")
    api_url = st.text_input("API URL", value=_api_url())
    st.session_state["api_url"] = api_url
    if st.button("Check Health"):
        try:
            h = httpx.get(f"{api_url}/health", timeout=12)
            st.success(f"API {h.status_code}")
        except Exception as e:
            st.error(str(e))
    if st.button("Automation Status"):
        try:
            s = httpx.get(f"{api_url}/system/automation/status", timeout=20)
            st.json(_safe_json(s))
        except Exception as e:
            st.error(str(e))

try:
    health = httpx.get(f"{api_url}/health", timeout=8)
    if health.status_code == 200:
        st.success(f"✅ Connected to API: {api_url}")
    else:
        st.warning(f"⚠️ API returned status={health.status_code}")
except Exception as e:
    st.error(f"❌ API not reachable: {e}")

l1_tab, l2_tab, l3_tab, layer_tab, pipeline_tab, outputs_tab = st.tabs([
    "L1 Intake",
    "L2 Resume Profile",
    "L3 Jobs",
    "L4-L10 Layer Runner",
    "One-Click Automation",
    "Outputs & Artifacts",
])

with l1_tab:
    st.subheader("L1 Intake + Bootstrap")
    if st.session_state.get("_l1_bootstrap_msg"):
        st.success(str(st.session_state.pop("_l1_bootstrap_msg")))
        st.info("L2 tab has been prefilled from your L1 intake resume.")
        st.json(st.session_state.pop("_l1_bootstrap_body", {}))
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Candidate Name", key="l1_name")
        roles = st.text_input("Target Roles (comma-separated)", value="ML Engineer, Backend Engineer", key="l1_roles")
        location = st.text_input("Preferred Location", value="USA", key="l1_loc")
        remote_only = st.checkbox("Remote only", value=True, key="l1_remote")
    with c2:
        salary_min = st.number_input("Salary Min", value=120000, step=5000, key="l1_smin")
        salary_max = st.number_input("Salary Max", value=180000, step=5000, key="l1_smax")
        work_auth = st.text_input("Work Authorization", value="OPT/H1B", key="l1_auth")
        resume_upload_l1 = st.file_uploader("Resume Upload (txt/pdf/docx)", type=["txt", "pdf", "docx", "png", "jpg", "jpeg", "webp", "bmp", "tiff"], key="l1_up")

    resume_text_l1 = st.text_area("Or paste resume text", height=160, key="l1_resume_text")

    if st.button("Create L1 Intake (with optional L2 bootstrap)"):
        target_roles = [r.strip() for r in roles.split(",") if r.strip()]
        resume_text = resume_text_l1.strip() or _upload_to_text(resume_upload_l1)
        try:
            if resume_text:
                payload = {
                    "candidate_name": name or None,
                    "target_roles": target_roles,
                    "location": location,
                    "remote_only": bool(remote_only),
                    "salary_min": int(salary_min),
                    "salary_max": int(salary_max),
                    "work_auth": work_auth or None,
                    "resume_text": resume_text,
                }
                r = httpx.post(f"{api_url}/intake/bootstrap", json=payload, timeout=30)
                body = _safe_json(r)
                _queue_l1_sync(name=name, resume_text=resume_text)
                st.session_state["_l1_bootstrap_body"] = body
                st.session_state["_l1_bootstrap_msg"] = "L1 + L2 bootstrap completed"
                st.rerun()
            else:
                payload = {
                    "version": "v1",
                    "candidate_name": name or None,
                    "target_roles": target_roles,
                    "constraints": {
                        "location": location,
                        "remote_only": bool(remote_only),
                        "salary_min": int(salary_min),
                        "salary_max": int(salary_max),
                        "work_auth": work_auth or None,
                        "relocation_ok": False,
                    },
                }
                r = httpx.post(f"{api_url}/intake", json=payload, timeout=20)
                st.info("Intake created. Add resume to auto-bootstrap profile.")
                st.json(_safe_json(r))
        except Exception as e:
            st.error(f"L1 failed: {e}")

with l2_tab:
    st.subheader("L2 Resume Parsing")
    st.caption("If you uploaded/pasted resume in L1, fields here are auto-filled.")
    c_name = st.text_input("Candidate Name", key="l2_name")
    c_resume = st.text_area("Resume Text", height=220, key="l2_resume")
    if st.button("Use latest L1 resume", key="l2_use_l1"):
        l1_text = (st.session_state.get("l1_resume_text") or "").strip()
        if not l1_text:
            l1_upload = st.session_state.get("l1_up")
            l1_text = _upload_to_text(l1_upload)
        _queue_l1_sync(name=st.session_state.get("l1_name", ""), resume_text=l1_text)
        st.success("L2 fields queued from L1 intake.")
        st.rerun()
    if st.button("Build Evidence Profile"):
        try:
            r = httpx.post(f"{api_url}/profile", json={"candidate_name": c_name or None, "resume_text": c_resume}, timeout=30)
            body = _safe_json(r)
            st.json(body)
            if isinstance(body, dict) and body.get("skills"):
                st.write("**Extracted Skills:**")
                st.write(", ".join(body["skills"]))
        except Exception as e:
            st.error(str(e))

with l3_tab:
    st.subheader("L3 Job Ingestion")
    st.caption("Automatic discovery is enabled for 8 job sources (LinkedIn, Indeed, Wellfound, Dice, BuiltIn, Glassdoor, ZipRecruiter, USAJobs).")

    manual_mode = st.toggle("Manual single-job ingest", value=False, key="l3_manual")
    if manual_mode:
        url = st.text_input("Job URL", key="l3_url")
        job_text = st.text_area("Job Description", height=220, key="l3_text")
        if st.button("Ingest Job"):
            try:
                r = httpx.post(f"{api_url}/jobs/ingest", json={"url": url or None, "job_text": job_text}, timeout=30)
                st.json(_safe_json(r))
            except Exception as e:
                st.error(str(e))
    else:
        roles_default = st.session_state.get("l1_roles", "ML Engineer, Backend Engineer")
        auto_roles = st.text_input("Target roles for auto-discovery (comma-separated)", value=roles_default, key="l3_roles")
        auto_location = st.text_input("Location", value=st.session_state.get("l1_loc", "USA"), key="l3_loc")
        c1, c2, c3 = st.columns(3)
        with c1:
            max_per_source = st.number_input("Max jobs/source", min_value=1, max_value=5, value=2, key="l3_mps")
        with c2:
            daily_limit = st.number_input("Daily ingest cap", min_value=1, max_value=60, value=20, key="l3_daily")
        with c3:
            recent_hours = st.number_input("Recent jobs within hours", min_value=1, max_value=240, value=36, key="l3_recent_hours")

        if st.button("Auto-discover + ingest jobs", key="l3_auto"):
            try:
                payload = {
                    "roles": [r.strip() for r in auto_roles.split(",") if r.strip()],
                    "location": auto_location,
                    "max_per_source": int(max_per_source),
                    "daily_limit": int(daily_limit),
                    "timeout_s": 10,
                    "recent_hours": int(recent_hours),
                }
                r = httpx.post(f"{api_url}/jobs/discover_ingest", json=payload, timeout=120)
                body = _safe_json(r)
                st.json(body)
                if isinstance(body, dict) and body.get("job_paths"):
                    st.success(f"Ingested {len(body['job_paths'])} jobs automatically.")
            except Exception as e:
                st.error(str(e))

with layer_tab:
    st.subheader("Run Individual Layers (L4-L10)")
    st.caption("Use this section for layer-wise debugging and manual progression.")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("L4 Match (latest profile + latest job)"):
        st.json(_safe_json(httpx.post(f"{api_url}/match/run", timeout=60)))
    top_n_ind = c2.number_input("L5 Top N", min_value=1, max_value=20, value=5, key="l5_top_n")
    if c2.button("L5 Rank"):
        st.json(_safe_json(httpx.post(f"{api_url}/rank/run", params={"top_n": int(top_n_ind)}, timeout=60)))
    if c3.button("L6 Generate Package"):
        st.json(_safe_json(httpx.post(f"{api_url}/generate/package", timeout=60)))
    if c4.button("L7 Guardrails Validate"):
        st.json(_safe_json(httpx.post(f"{api_url}/guardrails/validate", timeout=60)))

    st.markdown("### L8-L10 + Post-apply tracking")
    x1, x2, x3 = st.columns(3)
    run_id_hitl = x1.text_input("Run ID (for HITL approval)", key="l10_run_id")
    approved = x1.checkbox("Approved", value=False, key="l10_approved")
    reviewer = x1.text_input("Reviewer", value="human", key="l10_reviewer")
    if x1.button("L10 Save HITL Decision"):
        payload = {"run_id": run_id_hitl, "approved": bool(approved), "reviewer": reviewer}
        st.json(_safe_json(httpx.post(f"{api_url}/p22/approval/decision", json=payload, timeout=30)))

    if x2.button("P10 Generate Followups"):
        st.json(_safe_json(httpx.post(f"{api_url}/followups/generate", timeout=60)))
    if x2.button("P11 Generate Notifications"):
        st.json(_safe_json(httpx.post(f"{api_url}/notifications/generate", timeout=60)))

    if x3.button("Load Applications Metrics"):
        st.json(_safe_json(httpx.get(f"{api_url}/applications/metrics", timeout=30)))
    if x3.button("Load Applications List"):
        apps_resp = _safe_json(httpx.get(f"{api_url}/applications/list", timeout=30))
        st.json(apps_resp)
        items = apps_resp.get("items", []) if isinstance(apps_resp, dict) else []
        if items:
            import pandas as pd

            df = pd.DataFrame(items)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Applications CSV", data=csv, file_name="careeros_applications.csv", mime="text/csv")

with pipeline_tab:
    st.subheader("One-Click Full Automation (L1→L10)")
    c1, c2, c3 = st.columns(3)
    with c1:
        p25_candidate = st.text_input("Candidate", value="Demo Candidate", key="p25_candidate")
        p25_top_n = st.number_input("Top N", min_value=1, max_value=20, value=5, key="p25_top_n")
    with c2:
        roles = st.multiselect(
            "Target Roles",
            ["ML Engineer", "Data Scientist", "Backend Engineer", "GenAI Engineer", "Software Engineer", "AI Engineer"],
            default=["ML Engineer", "Backend Engineer", "GenAI Engineer"],
            key="p25_roles",
        )
        location = st.text_input("Discovery Location", value="USA", key="p25_location")
    with c3:
        daily_limit = st.number_input("Daily Job Cap", min_value=5, max_value=60, value=20, key="p25_cap")
        recent_hours = st.number_input("Recent jobs within hours", min_value=1, max_value=240, value=36, key="p25_recent_hours")
        private_mode = st.checkbox("Private Mode", value=True, key="p25_priv")

    resume_upload = st.file_uploader("Upload Resume for Automation", type=["txt", "pdf", "docx", "png", "jpg", "jpeg", "webp", "bmp", "tiff"], key="p25_upload")
    resume_inline = st.text_area("Or paste resume text", height=120, key="p25_resume_inline")

    if st.button("Run Full Automation"):
        if not resume_upload and not resume_inline.strip():
            st.warning("Please provide resume upload or text.")
        else:
            try:
                if resume_upload:
                    files = {
                        "resume_file": (resume_upload.name, resume_upload.getvalue(), resume_upload.type or "application/octet-stream")
                    }
                    data = {
                        "candidate_name": p25_candidate,
                        "top_n": int(p25_top_n),
                        "roles_csv": ",".join(roles),
                        "location": location,
                        "daily_limit": int(daily_limit),
                        "private_mode": str(bool(private_mode)).lower(),
                        "recent_hours": int(recent_hours),
                    }
                    resp = requests.post(f"{api_url}/p25/automation/run_upload_auto", files=files, data=data, timeout=300)
                    body = _safe_json(resp)
                else:
                    payload = {
                        "candidate_name": p25_candidate,
                        "top_n": int(p25_top_n),
                        "privacy": {"private_mode": bool(private_mode)},
                        "resume": {"source_type": "inline", "text": resume_inline.strip()},
                        "jobs": {
                            "auto_discover": True,
                            "daily_limit": int(daily_limit),
                            "max_per_source": 2,
                            "preferences": {"roles": roles, "location": location, "recent_hours": int(recent_hours)},
                        },
                    }
                    resp = httpx.post(f"{api_url}/p25/automation/run", json=payload, timeout=300)
                    body = _safe_json(resp)

                st.json(body)
                if isinstance(body, dict) and body.get("status") == "ok":
                    m = body.get("metrics", {})
                    hitl = body.get("hitl", {})
                    col_a, col_b, col_c, col_d = st.columns(4)
                    col_a.metric("Match Score", f"{round(float(m.get('match_score', 0))*100, 1)}%")
                    col_b.metric("Jobs Ingested", m.get("jobs_ingested", 0))
                    col_c.metric("Guardrails", m.get("guardrails_status", "n/a"))
                    col_d.metric("Vector Backend", body.get("vector_store", {}).get("backend", "n/a"))
                    st.markdown("### Explainable Summary")
                    st.write(body.get("llm_summary", {}).get("text", "No summary generated."))
                    rec = body.get("recommendation", {})
                    qg = body.get("quality_gate", {})
                    st.markdown("### Recommendation")
                    st.write(f"Recommended: **{rec.get('recommended')}**")
                    for why in rec.get("why_recommended", []):
                        st.write(f"✅ {why}")
                    for why_not in rec.get("why_not", []):
                        st.write(f"⚠️ {why_not}")
                    st.markdown("### Output Quality Gate")
                    st.write(f"Status: **{qg.get('status', 'n/a')}**")
                    for issue in qg.get("issues", []):
                        st.write(f"- {issue}")
                    st.markdown("### HITL Decision")
                    st.write(f"Approval Required: **{hitl.get('approval_required')}**")
                    for reason in hitl.get("reasons", []):
                        st.write(f"- {reason}")
                    _render_layer_timeline(body)
            except Exception as e:
                st.error(f"Automation failed: {e}")

with outputs_tab:
    st.subheader("Artifacts + System State")
    if st.button("Load System Storage Status"):
        try:
            s = httpx.get(f"{api_url}/system/storage/status", timeout=20)
            st.json(_safe_json(s))
        except Exception as e:
            st.error(str(e))

    if st.button("Load Automation/Integrations Status"):
        try:
            s = httpx.get(f"{api_url}/system/automation/status", timeout=20)
            st.json(_safe_json(s))
        except Exception as e:
            st.error(str(e))

    if st.button("Load System Architecture Map"):
        try:
            s = httpx.get(f"{api_url}/system/architecture/map", timeout=20)
            st.json(_safe_json(s))
        except Exception as e:
            st.error(str(e))

    p25_run_id = st.text_input("Run ID for latest layer report (optional)", key="out_run_id")
    if st.button("Load Latest P25 Layer Report"):
        try:
            params = {"run_id": p25_run_id.strip()} if p25_run_id.strip() else None
            s = httpx.get(f"{api_url}/p25/automation/layers/latest", params=params, timeout=30)
            body = _safe_json(s)
            st.json(body)
            if isinstance(body, dict) and body.get("layers"):
                st.markdown("### P25 Layer Status")
                for row in body.get("layers", []):
                    st.write(f"- **{row.get('layer')}** → `{row.get('status')}`")
        except Exception as e:
            st.error(str(e))

    if st.button("Share Latest Artifacts to transfer.sh"):
        try:
            s = httpx.post(f"{api_url}/artifacts/share/latest", json={}, timeout=90)
            st.json(_safe_json(s))
        except Exception as e:
            st.error(str(e))

    artifact_path = st.text_input("Artifact path")
    if st.button("Open Artifact") and artifact_path.strip():
        encoded = quote(artifact_path.strip(), safe="")
        st.markdown(f"[Open file]({api_url}/artifacts/open?path={encoded})")
        try:
            rr = httpx.get(f"{api_url}/artifacts/read", params={"path": artifact_path.strip()}, timeout=20)
            st.json(_safe_json(rr))
        except Exception as e:
            st.error(str(e))
