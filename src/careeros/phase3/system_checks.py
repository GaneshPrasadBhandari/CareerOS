from __future__ import annotations

import importlib.util
import sqlite3
from pathlib import Path
from typing import Any

import httpx


def _check_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def run_system_health_checks() -> dict[str, Any]:
    ollama_url = "http://127.0.0.1:11434"
    ollama_ok = False
    ollama_error = None
    try:
        r = httpx.get(f"{ollama_url}/api/tags", timeout=3)
        ollama_ok = r.status_code == 200
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
        "orchestration": {
            "langgraph_installed": _check_module("langgraph"),
        },
        "llm": {
            "ollama_reachable": ollama_ok,
            "ollama_url": ollama_url,
            "error": ollama_error,
            "huggingface_support_installed": _check_module("transformers"),
        },
        "vector_db": {
            "chromadb_installed": _check_module("chromadb"),
            "chromadb_ephemeral_ok": chroma_ok,
            "error": chroma_error,
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
            ],
        },
    }

    overall_ok = (
        checks["storage"]["sqlite_ok"]
        and checks["orchestration"]["langgraph_installed"]
        and checks["vector_db"]["chromadb_installed"]
    )

    return {"status": "ok" if overall_ok else "degraded", "checks": checks}
