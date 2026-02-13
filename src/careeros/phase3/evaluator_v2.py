from __future__ import annotations

import glob
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class EvalWeights:
    match_quality: int = 30
    guardrails_quality: int = 25
    approval_quality: int = 20
    package_quality: int = 15
    pipeline_reliability: int = 10


def _stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def _latest(pattern: str) -> str | None:
    files = glob.glob(pattern)
    if not files:
        return None
    return str(max(files, key=lambda f: Path(f).stat().st_mtime))


def _load_json(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _score_match(run_id: str) -> tuple[int, dict[str, Any]]:
    shortlist_path = _latest(f"outputs/ranking/shortlist_{run_id}_*.json")
    if not shortlist_path:
        return 0, {"status": "missing_shortlist", "path": None}
    data = _load_json(shortlist_path)
    items = data.get("items", [])
    top_score = float(items[0].get("score", 0.0)) if items else 0.0
    return int(round(top_score)), {"status": "ok", "path": shortlist_path, "top_score": top_score}


def _score_guardrails() -> tuple[int, dict[str, Any]]:
    report_path = _latest("outputs/guardrails/validation_report_v1_*.json")
    if not report_path:
        return 0, {"status": "missing_validation", "path": None}
    data = _load_json(report_path)
    status = data.get("status")
    findings = data.get("findings", [])
    if status == "pass":
        return 100, {"status": "pass", "path": report_path, "findings": len(findings)}
    return 25, {"status": status or "blocked", "path": report_path, "findings": len(findings)}


def _score_approval(run_id: str) -> tuple[int, dict[str, Any]]:
    ap_path = _latest(f"outputs/phase3/p22_approval_{run_id}_*.json")
    if not ap_path:
        return 50, {"status": "missing_approval", "path": None}
    data = _load_json(ap_path)
    approved = bool(data.get("approved"))
    notes = str(data.get("notes") or "").strip()
    base = 100 if approved else 40
    if notes:
        base = min(100, base + 10)
    return base, {"status": "approved" if approved else "rejected", "path": ap_path, "notes_present": bool(notes)}


def _score_package(run_id: str) -> tuple[int, dict[str, Any]]:
    pkg_path = _latest("exports/packages/application_package_*.json")
    if not pkg_path:
        return 0, {"status": "missing_package", "path": None}
    data = _load_json(pkg_path)
    bullets = data.get("bullets", [])
    qa = data.get("qa_stubs", {})
    score = min(100, len(bullets) * 25 + (10 if isinstance(qa, dict) and qa else 0))
    return score, {"status": "ok", "path": pkg_path, "bullets": len(bullets)}


def _score_reliability(run_id: str) -> tuple[int, dict[str, Any]]:
    checks = {
        "profile": bool(_latest("outputs/profile/profile_v1_*.json")),
        "job": bool(_latest("outputs/jobs/job_post_v1_*.json")),
        "match": bool(_latest("outputs/matching/match_result_v1_*.json")),
        "shortlist": bool(_latest(f"outputs/ranking/shortlist_{run_id}_*.json")),
        "validation": bool(_latest("outputs/guardrails/validation_report_v1_*.json")),
    }
    hit = sum(int(v) for v in checks.values())
    return int((hit / len(checks)) * 100), {"checks": checks, "hit": hit, "total": len(checks)}


def evaluate_run_v2(run_id: str, weights: EvalWeights | None = None) -> dict[str, Any]:
    w = weights or EvalWeights()

    raw_match, ev_match = _score_match(run_id)
    raw_guard, ev_guard = _score_guardrails()
    raw_approval, ev_approval = _score_approval(run_id)
    raw_package, ev_package = _score_package(run_id)
    raw_reliability, ev_reliability = _score_reliability(run_id)

    weighted = {
        "match_quality": round((raw_match / 100.0) * w.match_quality, 2),
        "guardrails_quality": round((raw_guard / 100.0) * w.guardrails_quality, 2),
        "approval_quality": round((raw_approval / 100.0) * w.approval_quality, 2),
        "package_quality": round((raw_package / 100.0) * w.package_quality, 2),
        "pipeline_reliability": round((raw_reliability / 100.0) * w.pipeline_reliability, 2),
    }

    overall = round(sum(weighted.values()), 2)
    risk_level = "low" if overall >= 75 else "medium" if overall >= 45 else "high"

    recommendations: list[str] = []
    if raw_match < 50:
        recommendations.append("Improve profile/job skill extraction coverage before ranking.")
    if raw_guard < 100:
        recommendations.append("Resolve guardrails blockers in generated package.")
    if raw_approval < 100:
        recommendations.append("Capture explicit approval with reviewer notes for audit quality.")

    out = {
        "run_id": run_id,
        "kpi_breakdown": {
            "raw": {
                "match_quality": raw_match,
                "guardrails_quality": raw_guard,
                "approval_quality": raw_approval,
                "package_quality": raw_package,
                "pipeline_reliability": raw_reliability,
            },
            "weighted": weighted,
        },
        "overall_score": overall,
        "risk_level": risk_level,
        "recommendations": recommendations,
        "evidence_paths": {
            "match": ev_match.get("path"),
            "guardrails": ev_guard.get("path"),
            "approval": ev_approval.get("path"),
            "package": ev_package.get("path"),
        },
        "evidence_meta": {
            "match": ev_match,
            "guardrails": ev_guard,
            "approval": ev_approval,
            "package": ev_package,
            "reliability": ev_reliability,
        },
        "weights": w.__dict__,
        "ts": _stamp(),
    }

    out_dir = Path("outputs/phase3")
    out_dir.mkdir(parents=True, exist_ok=True)
    fp = out_dir / f"p24_eval_v2_{run_id}_{out['ts']}.json"
    fp.write_text(json.dumps(out, indent=2), encoding="utf-8")

    return {"status": "ok", "summary": out, "path": str(fp)}


def latest_eval_v2(run_id: str) -> dict[str, Any]:
    fp = _latest(f"outputs/phase3/p24_eval_v2_{run_id}_*.json")
    if not fp:
        return {"status": "idle", "message": f"No evaluator v2 artifact found for run_id={run_id}"}
    return {"status": "ok", "path": fp, "summary": _load_json(fp)}
