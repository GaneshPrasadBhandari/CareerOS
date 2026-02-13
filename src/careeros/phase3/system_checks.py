from __future__ import annotations

import importlib.util
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx


def _check_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_system_health_checks() -> dict[str, Any]:
    ts = _utc_now_iso()

    ollama_url = "http://127.0.0.1:11434"
    ollama_ok = False
    ollama_error = None
    ollama_models: list[str] = []
    try:
        r = httpx.get(f"{ollama_url}/api/tags", timeout=3)
        ollama_ok = r.status_code == 200
        if ollama_ok:
            payload = r.json()
            ollama_models = [m.get("name", "") for m in payload.get("models", []) if m.get("name")]
    except Exception as e:
        ollama_error = str(e)

    db_path = Path("outputs/phase3/system_state.sqlite")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_ok = True
    db_error = None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("create table if not exists health_ping(ts text, status text)")
        cur.execute("insert into health_ping(ts, status) values(datetime('now'), 'ok')")
        conn.commit()
        conn.close()
    except Exception as e:
        db_ok = False
        db_error = str(e)

    chroma_ok = False
    chroma_error = None
    try:
        import chromadb

        client = chromadb.EphemeralClient()
        col = client.get_or_create_collection("careeros_health")
        chroma_ok = col is not None
    except Exception as e:
        chroma_error = str(e)

    checks = {
        "timestamp_utc": ts,
        "orchestration": {
            "langgraph_installed": _check_module("langgraph"),
        },
        "llm": {
            "ollama_reachable": ollama_ok,
            "ollama_url": ollama_url,
            "available_models": ollama_models,
            "error": ollama_error,
            "huggingface_support_installed": _check_module("transformers"),
            "sentence_transformers_installed": _check_module("sentence_transformers"),
        },
        "vector_db": {
            "chromadb_installed": _check_module("chromadb"),
            "chromadb_ephemeral_ok": chroma_ok,
            "qdrant_client_installed": _check_module("qdrant_client"),
            "faiss_installed": _check_module("faiss"),
            "error": chroma_error,
        },
        "document_tools": {
            "pypdf_installed": _check_module("pypdf"),
            "python_docx_installed": _check_module("docx"),
            "unstructured_installed": _check_module("unstructured"),
            "pytesseract_installed": _check_module("pytesseract"),
            "tesseract_binary_found": shutil.which("tesseract") is not None,
        },
        "storage": {
            "sqlite_ok": db_ok,
            "sqlite_path": str(db_path),
            "error": db_error,
        },
        "agents": {
            "implemented": [
                "context_loader",
                "matcher",
                "ranker",
                "generator",
                "guardrails",
                "approval",
                "memory",
                "evaluator",
                "parser_stub",
                "vision_stub",
                "connector_stub",
            ],
            "planned_upgrade": [
                "parser_v1_pdf_docx",
                "vision_ocr_real",
                "connector_api_ingest",
                "evaluator_v2_weighted",
                "embedding_provider_adapter",
            ],
        },
    }

    overall_ok = (
        checks["storage"]["sqlite_ok"]
        and checks["orchestration"]["langgraph_installed"]
        and checks["vector_db"]["chromadb_installed"]
    )

    artifact_dir = Path("outputs/phase3/p25_system_checks")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / f"system_health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    payload = {
        "status": "ok" if overall_ok else "degraded",
        "checks": checks,
        "artifact_path": str(artifact_path),
    }
    artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
