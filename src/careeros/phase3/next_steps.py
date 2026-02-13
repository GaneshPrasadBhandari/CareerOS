from __future__ import annotations

import glob
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def _latest(pattern: str) -> str | None:
    files = glob.glob(pattern)
    if not files:
        return None
    return str(max(files, key=lambda f: Path(f).stat().st_mtime))


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
    text = (payload.get("text") or "").strip()
    return {
        "status": "ok",
        "agent": "parser",
        "source_type": payload.get("source_type", "inline"),
        "extracted_text": text,
        "char_count": len(text),
        "notes": ["Deterministic parser stub for P22/P23 expansion"],
    }


def vision_ocr(payload: dict[str, Any]) -> dict[str, Any]:
    text = payload.get("mock_ocr_text") or "OCR output placeholder"
    return {
        "status": "ok",
        "agent": "vision",
        "recognized_text": text,
        "notes": ["Vision/OCR stub endpoint; integrate model in next phase"],
    }


def connector_ingest(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "ok",
        "agent": "connector",
        "source": payload.get("source", "manual_import"),
        "items_ingested": int(payload.get("items_ingested", 1)),
        "notes": ["Connector stub endpoint; use official APIs/compliant ingestion in production"],
    }
