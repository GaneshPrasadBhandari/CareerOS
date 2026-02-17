from __future__ import annotations

import glob
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
import os

import httpx

from careeros.generation.service import build_package, write_application_package
from careeros.guardrails.service import validate_package_against_evidence, write_validation_report
from careeros.jobs.service import build_jobpost_from_text, write_jobpost
from careeros.matching.service import compute_match, write_match_result
from careeros.parsing.schema import EvidenceProfile
from careeros.parsing.service import build_profile_from_text, extract_skills, write_profile
from careeros.ranking.service import rank_all_jobs, write_shortlist


def _stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def _latest(pattern: str) -> str | None:
    files = glob.glob(pattern)
    if not files:
        return None
    return str(max(files, key=lambda f: Path(f).stat().st_mtime))


def _read_resume_text(payload: dict[str, Any]) -> tuple[str, list[str]]:
    notes: list[str] = []
    source_type = str(payload.get("source_type", "inline")).lower()
    text = (payload.get("text") or payload.get("resume_text") or "").strip()
    source_path = payload.get("source_path")

    if text:
        return text, notes

    if not source_path:
        return "", ["No text/source_path provided"]

    p = Path(source_path)
    if not p.exists():
        return "", [f"source_path not found: {source_path}"]

    if source_type in {"txt", "text", "inline"}:
        return p.read_text(encoding="utf-8", errors="ignore"), notes

    if source_type == "pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(p))
            chunks = [(pg.extract_text() or "") for pg in reader.pages]
            return "\n".join(chunks).strip(), notes
        except Exception as e:
            return "", [f"pdf parse failed: {e}"]

    if source_type in {"docx", "doc"}:
        try:
            from docx import Document

            doc = Document(str(p))
            return "\n".join(par.text for par in doc.paragraphs).strip(), notes
        except Exception as e:
            return "", [f"docx parse failed: {e}"]

    return p.read_text(encoding="utf-8", errors="ignore"), [f"fallback text read for source_type={source_type}"]


def write_p22_approval_decision(*, run_id: str, approved: bool, reviewer: str = "human", notes: str | None = None) -> dict[str, Any]:
    out_dir = Path("outputs/phase3")
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "approved": bool(approved),
        "reviewer": reviewer,
        "notes": notes or "",
        "status": "approved" if approved else "rejected",
        "ts": _stamp(),
    }
    fp = out_dir / f"p22_approval_{run_id}_{payload['ts']}.json"
    fp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    payload["path"] = str(fp)
    return payload


def latest_p22_approval(run_id: str) -> dict[str, Any]:
    fp = _latest(f"outputs/phase3/p22_approval_{run_id}_*.json")
    if not fp:
        return {"status": "idle", "message": f"No approval decision found for run_id={run_id}"}
    return json.loads(Path(fp).read_text(encoding="utf-8")) | {"path": fp, "status": "ok"}


def p23_memory_upsert(*, run_id: str, namespace: str, key: str, value: Any) -> dict[str, Any]:
    out_dir = Path("outputs/phase3")
    out_dir.mkdir(parents=True, exist_ok=True)
    fp = out_dir / f"p23_memory_{run_id}.json"
    data: dict[str, Any] = {}
    if fp.exists():
        data = json.loads(fp.read_text(encoding="utf-8"))
    data.setdefault(namespace, {})
    data[namespace][key] = value
    data["_meta"] = {"updated_at": _stamp(), "run_id": run_id}
    fp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return {"status": "ok", "run_id": run_id, "namespace": namespace, "key": key, "path": str(fp)}


def p23_memory_get(*, run_id: str, namespace: str, key: str) -> dict[str, Any]:
    fp = Path(f"outputs/phase3/p23_memory_{run_id}.json")
    if not fp.exists():
        return {"status": "idle", "message": f"No memory file for run_id={run_id}"}
    data = json.loads(fp.read_text(encoding="utf-8"))
    ns = data.get(namespace, {})
    if key not in ns:
        return {"status": "missing", "message": f"Key not found: {namespace}.{key}", "path": str(fp)}
    return {"status": "ok", "run_id": run_id, "namespace": namespace, "key": key, "value": ns[key], "path": str(fp)}


def p24_evaluate_run(run_id: str) -> dict[str, Any]:
    result_fp = _latest(f"outputs/ranking/shortlist_{run_id}_*.json")
    approval_fp = _latest(f"outputs/phase3/p22_approval_{run_id}_*.json")
    validation_fp = _latest("outputs/guardrails/validation_report_v1_*.json")

    summary = {
        "run_id": run_id,
        "has_shortlist": bool(result_fp),
        "has_approval": bool(approval_fp),
        "has_validation": bool(validation_fp),
        "score": 0,
    }
    summary["score"] = int(summary["has_shortlist"]) + int(summary["has_validation"]) + int(summary["has_approval"])

    out_dir = Path("outputs/phase3")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_fp = out_dir / f"p24_eval_{run_id}_{_stamp()}.json"
    out_fp.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {"status": "ok", "summary": summary, "path": str(out_fp)}


def parser_extract(payload: dict[str, Any]) -> dict[str, Any]:
    text, notes = _read_resume_text(payload)
    skills = extract_skills(text) if text else []
    section_hits = {
        "skills": int(bool(re.search(r"\bskills\b", text, re.IGNORECASE))),
        "experience": int(bool(re.search(r"\bexperience\b", text, re.IGNORECASE))),
        "education": int(bool(re.search(r"\beducation\b", text, re.IGNORECASE))),
    }

    out_dir = Path("outputs/phase3/parser")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_fp = out_dir / f"parsed_resume_{_stamp()}.json"
    artifact = {
        "status": "ok" if text else "error",
        "agent": "parser",
        "source_type": payload.get("source_type", "inline"),
        "char_count": len(text),
        "skills": skills,
        "section_hits": section_hits,
        "notes": notes,
    }
    out_fp.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

    return {
        **artifact,
        "extracted_text": text,
        "path": str(out_fp),
    }


def vision_ocr(payload: dict[str, Any]) -> dict[str, Any]:
    mock = payload.get("mock_ocr_text")
    if mock:
        return {
            "status": "ok",
            "agent": "vision",
            "recognized_text": mock,
            "notes": ["Used mock_ocr_text"],
        }

    image_path = payload.get("image_path")
    if not image_path:
        return {"status": "error", "agent": "vision", "recognized_text": "", "notes": ["Missing image_path"]}

    try:
        import pytesseract
        from PIL import Image

        text = pytesseract.image_to_string(Image.open(image_path)).strip()
        return {
            "status": "ok",
            "agent": "vision",
            "recognized_text": text,
            "notes": ["OCR executed with pytesseract"],
        }
    except Exception as e:
        return {
            "status": "degraded",
            "agent": "vision",
            "recognized_text": "",
            "notes": [f"OCR unavailable: {e}"],
        }


def _html_to_text(html: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def connector_ingest(payload: dict[str, Any]) -> dict[str, Any]:
    # backward-compatible stub mode
    if "items_ingested" in payload and not payload.get("urls"):
        return {
            "status": "ok",
            "agent": "connector",
            "source": payload.get("source", "manual_import"),
            "items_ingested": int(payload.get("items_ingested", 1)),
            "notes": ["Compatibility mode: deterministic connector stub"],
        }

    urls: list[str] = [u for u in payload.get("urls", []) if u]
    timeout_s = int(payload.get("timeout_s", 8))
    items: list[dict[str, Any]] = []
    errors: list[str] = []

    for url in urls:
        try:
            r = httpx.get(url, timeout=timeout_s, follow_redirects=True)
            r.raise_for_status()
            txt = _html_to_text(r.text)
            items.append({"url": url, "text": txt[:12000], "char_count": len(txt)})
        except Exception as e:
            errors.append(f"{url}: {e}")

    out_dir = Path("outputs/phase3/connectors")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_fp = out_dir / f"connector_ingest_{_stamp()}.json"
    out_fp.write_text(json.dumps({"items": items, "errors": errors}, indent=2), encoding="utf-8")

    return {
        "status": "ok" if items else "degraded",
        "agent": "connector",
        "items_ingested": len(items),
        "items": items,
        "errors": errors,
        "path": str(out_fp),
    }


# def _ollama_summary(run_id: str, score: float) -> dict[str, Any]:
#     prompt = (
#         "You are a career assistant. Summarize this run in 3 bullet points and suggest 2 next actions. "
#         f"Run ID: {run_id}. Match score: {score}. Keep it concise."
#     )
#     body = {"model": "llama3.1:8b-instruct", "prompt": prompt, "stream": False}
#     try:
#         r = httpx.post("http://127.0.0.1:11434/api/generate", json=body, timeout=20)
#         if r.status_code == 200:
#             return {"status": "ok", "provider": "ollama", "text": r.json().get("response", "")}
#     except Exception as e:
#         return {"status": "degraded", "provider": "ollama", "text": "", "error": str(e)}
#     return {"status": "degraded", "provider": "ollama", "text": "", "error": f"HTTP {r.status_code}"}


# 


# def _ollama_summary(run_id: str, score: float) -> dict[str, Any]:
#     """
#     FIXED: Resolves 'Connection Refused' by using localhost and 
#     correcting the model name to match your local setup.
#     """
#     # 1. Use localhost for better Mac compatibility
#     base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
#     ollama_endpoint = f"{base_url}/api/generate"
    
#     prompt = (
#         "You are a career assistant. Summarize this run in 3 short bullet points "
#         "and suggest 2 next actions based on the match score. "
#         f"Run ID: {run_id}. Match score: {score}. Keep it concise."
#     )
    
#     # 2. Use 'llama3' as seen in your 'ollama list'
#     body = {
#         "model": "llama3", 
#         "prompt": prompt, 
#         "stream": False
#     }
    
#     try:
#         # 3. 30s timeout to allow for model loading/cold start
#         r = httpx.post(ollama_endpoint, json=body, timeout=30.0)
        
#         if r.status_code == 200:
#             return {
#                 "status": "ok", 
#                 "provider": "ollama", 
#                 "text": r.json().get("response", "")
#             }
        
#         return {
#             "status": "degraded", 
#             "provider": "ollama", 
#             "text": "", 
#             "error": f"HTTP {r.status_code} - Is Ollama server healthy?"
#         }
        
#     except Exception as e:
#         return {
#             "status": "degraded", 
#             "provider": "ollama", 
#             "text": "", 
#             "error": f"Connection failed to {ollama_endpoint}: {str(e)}"
#         }



# def _ollama_summary(run_id: str, score: float) -> dict[str, Any]:
#     # 1. MATCH THE LOGS: Use the exact IP Ollama is listening on
#     # We use 127.0.0.1 because your log said: "Listening on 127.0.0.1:11434"
#     ollama_url = "http://127.0.0.1:11434/api/generate"
    
#     prompt = (
#         "You are a career assistant. Summarize this run in 3 short bullet points "
#         "and suggest 2 next actions based on the match score. "
#         f"Run ID: {run_id}. Match score: {score}. Keep it concise."
#     )
    
#     # 2. ENSURE MODEL MATCH: Using 'llama3' which we saw in your 'ollama list'
#     body = {
#         "model": "llama3", 
#         "prompt": prompt, 
#         "stream": False
#     }
    
#     try:
#         # 3. Increased timeout to 60s because your logs show only 5.7 GiB 
#         # of available RAM—it might take a moment to load the model.
#         r = httpx.post(ollama_url, json=body, timeout=60.0)
        
#         if r.status_code == 200:
#             return {
#                 "status": "ok", 
#                 "provider": "ollama", 
#                 "text": r.json().get("response", "")
#             }
#         return {"status": "degraded", "error": f"Ollama returned {r.status_code}"}
        
#     except Exception as e:
#         return {"status": "degraded", "error": str(e)}


from careeros.orchestration.router import generate_summary_with_fallback

def _ollama_summary(run_id: str, score: float) -> dict[str, Any]:
    return generate_summary_with_fallback(run_id=run_id, score=score)




def _write_p25_trace(run_id: str, trace: dict[str, Any]) -> str:
    out_dir = Path("outputs/phase3/p25_runs")
    out_dir.mkdir(parents=True, exist_ok=True)
    fp = out_dir / f"p25_trace_{run_id}_{_stamp()}.json"
    fp.write_text(json.dumps(trace, indent=2), encoding="utf-8")
    return str(fp)


def latest_p25_trace(run_id: str | None = None) -> dict[str, Any]:
    pattern = f"outputs/phase3/p25_runs/p25_trace_{run_id}_*.json" if run_id else "outputs/phase3/p25_runs/p25_trace_*.json"
    fp = _latest(pattern)
    if not fp:
        return {"status": "idle", "message": "No P25 trace artifact found"}
    return {"status": "ok", "path": fp, "trace": json.loads(Path(fp).read_text(encoding="utf-8"))}


def p25_automation_run(payload: dict[str, Any]) -> dict[str, Any]:
    run_id = str(payload.get("run_id") or f"p25_{_stamp()}")
    candidate_name = payload.get("candidate_name")
    top_n = int(payload.get("top_n", 3))

    parse_result = parser_extract(payload.get("resume") or {})
    resume_text = parse_result.get("extracted_text", "")
    if not resume_text:
        return {"status": "error", "run_id": run_id, "message": "Resume text could not be extracted", "parser": parse_result}

    profile = build_profile_from_text(resume_text, candidate_name=candidate_name)
    profile_path = str(write_profile(profile))

    jobs_payload = payload.get("jobs") or {}
    ingested_jobs: list[str] = []

    for jt in jobs_payload.get("job_texts", []):
        if isinstance(jt, str) and jt.strip():
            ingested_jobs.append(str(write_jobpost(build_jobpost_from_text(jt.strip()))))

    conn_result = connector_ingest({"urls": jobs_payload.get("urls", []), "timeout_s": jobs_payload.get("timeout_s", 8)})
    for item in conn_result.get("items", []):
        txt = (item.get("text") or "").strip()
        if txt:
            ingested_jobs.append(str(write_jobpost(build_jobpost_from_text(txt, url=item.get("url")))))

    if not ingested_jobs:
        return {
            "status": "error",
            "run_id": run_id,
            "message": "No jobs were ingested. Provide jobs.job_texts or reachable jobs.urls",
            "profile_path": profile_path,
            "parser": parse_result,
            "connector": conn_result,
        }

    first_job_path = ingested_jobs[0]
    job_obj = json.loads(Path(first_job_path).read_text(encoding="utf-8"))
    job_model = build_jobpost_from_text(job_obj.get("raw_text", ""), url=job_obj.get("url"))
    match = compute_match(profile, job_model, run_id=run_id, profile_path=profile_path, job_path=first_job_path)
    match_path = str(write_match_result(match))

    shortlist = rank_all_jobs(profile_path=profile_path, top_n=top_n, run_id=run_id, job_paths=ingested_jobs)
    shortlist_path = str(write_shortlist(shortlist))

    top_item = shortlist.items[0]
    top_job_path = top_item.job_path
    top_job_raw = json.loads(Path(top_job_path).read_text(encoding="utf-8"))
    top_job_model = build_jobpost_from_text(top_job_raw.get("raw_text", ""), url=top_job_raw.get("url"))

    pkg = build_package(
        profile=profile,
        job=top_job_model,
        run_id=run_id,
        profile_path=profile_path,
        job_path=top_job_path,
        overlap_skills=top_item.overlap_skills,
    )
    package_path = str(write_application_package(pkg))

    report = validate_package_against_evidence(
        profile=profile,
        pkg=pkg,
        run_id=run_id,
        package_path=package_path,
    )
    validation_path = str(write_validation_report(report))

    llm_summary = _ollama_summary(run_id=run_id, score=match.score)

    trace = {
        "run_id": run_id,
        "layers": {
            "L2_parsing": {
                "agent": "parser",
                "input": {"resume_source": (payload.get("resume") or {}).get("source_type", "inline")},
                "output": {"profile_path": profile_path, "skills": profile.skills},
                "next_layer": "L3_jobs",
            },
            "L3_jobs": {
                "agent": "connector",
                "input": {"job_text_count": len(jobs_payload.get("job_texts") or []), "urls": jobs_payload.get("urls", [])},
                "output": {"jobs_ingested": len(ingested_jobs), "first_job_path": first_job_path},
                "next_layer": "L4_matching",
            },
            "L4_matching": {
                "agent": "matcher",
                "input": {"profile_path": profile_path, "job_path": first_job_path},
                "output": {"match_path": match_path, "match_score": match.score},
                "next_layer": "L5_ranking",
            },
            "L5_ranking": {
                "agent": "ranker",
                "input": {"top_n": top_n},
                "output": {"shortlist_path": shortlist_path, "ranked_items": len(shortlist.items)},
                "next_layer": "L6_generation",
            },
            "L6_generation": {
                "agent": "generator",
                "input": {"top_job_path": top_job_path},
                "output": {"package_path": package_path},
                "next_layer": "L7_guardrails",
            },
            "L7_guardrails": {
                "agent": "guardrails",
                "input": {"package_path": package_path},
                "output": {"validation_report_path": validation_path, "status": report.status},
                "next_layer": "L8_summary",
            },
            "L8_summary": {
                "agent": "llm_summary",
                "input": {"provider": "ollama", "run_id": run_id},
                "output": {"status": llm_summary.get("status", "degraded")},
                "next_layer": "completed",
            },
        },
    }
    trace_path = _write_p25_trace(run_id, trace)

    return {
        "status": "ok",
        "run_id": run_id,
        "parser": {k: v for k, v in parse_result.items() if k != "extracted_text"},
        "connector": {k: v for k, v in conn_result.items() if k != "items"},
        "paths": {
            "profile_path": profile_path,
            "first_job_path": first_job_path,
            "match_path": match_path,
            "shortlist_path": shortlist_path,
            "package_path": package_path,
            "validation_report_path": validation_path,
            "trace_path": trace_path,
        },
        "metrics": {
            "match_score": match.score,
            "ranked_items": len(shortlist.items),
            "guardrails_status": report.status,
            "jobs_ingested": len(ingested_jobs),
        },
        "llm_summary": llm_summary,
        "trace": trace,
    }
