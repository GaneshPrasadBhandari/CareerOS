from __future__ import annotations

import io
from urllib.parse import quote

import httpx
import requests
import streamlit as st

st.set_page_config(page_title="CareerOS", layout="wide")
st.title("CareerOS — End-to-End Job Automation Dashboard")
st.caption("L1 Intake → L2 Parse → L3 Discover/Ingest Jobs → L4 Match → L5 Rank → L6 Generate → L7 Guardrails → L8 Summary + Vector DB")


def _api_url() -> str:
    cloud_api_url = st.secrets.get("API_URL") or st.secrets.get("BACKEND_URL") or "https://careeros-backend-d9sc.onrender.com"
    if "api_url" not in st.session_state:
        st.session_state["api_url"] = cloud_api_url
    return st.session_state["api_url"]


def _upload_to_text(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    name = (uploaded_file.name or "").lower()
    raw = uploaded_file.getvalue()
    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(raw))
            return "\n".join((p.extract_text() or "") for p in reader.pages).strip()
        except Exception:
            return raw.decode("utf-8", errors="ignore").strip()
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


def _safe_json(resp: requests.Response | httpx.Response):
    try:
        return resp.json()
    except Exception:
        return {"status": "error", "message": resp.text}


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

l1_tab, l2_tab, l3_tab, pipeline_tab, outputs_tab = st.tabs([
    "L1 Intake",
    "L2 Resume Profile",
    "L3 Jobs",
    "L4-L10 Automation",
    "Outputs & Artifacts",
])

with l1_tab:
    st.subheader("L1 Intake + Bootstrap")
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
                st.success("L1 + L2 bootstrap completed")
                st.json(_safe_json(r))
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
    c_name = st.text_input("Candidate Name", key="l2_name")
    c_resume = st.text_area("Resume Text", height=220, key="l2_resume")
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
    url = st.text_input("Job URL", key="l3_url")
    job_text = st.text_area("Job Description", height=220, key="l3_text")
    if st.button("Ingest Job"):
        try:
            r = httpx.post(f"{api_url}/jobs/ingest", json={"url": url or None, "job_text": job_text}, timeout=30)
            st.json(_safe_json(r))
        except Exception as e:
            st.error(str(e))

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
                            "preferences": {"roles": roles, "location": location},
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
                    st.markdown("### HITL Decision")
                    st.write(f"Approval Required: **{hitl.get('approval_required')}**")
                    for reason in hitl.get("reasons", []):
                        st.write(f"- {reason}")
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

    artifact_path = st.text_input("Artifact path")
    if st.button("Open Artifact") and artifact_path.strip():
        encoded = quote(artifact_path.strip(), safe="")
        st.markdown(f"[Open file]({api_url}/artifacts/open?path={encoded})")
        try:
            rr = httpx.get(f"{api_url}/artifacts/read", params={"path": artifact_path.strip()}, timeout=20)
            st.json(_safe_json(rr))
        except Exception as e:
            st.error(str(e))
