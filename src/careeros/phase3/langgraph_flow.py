"""P21 LangGraph workflow (deterministic implementation).

This module wires existing deterministic services into a LangGraph state machine.
The goal is to validate orchestration behavior before enabling live LLM/tool routing.
"""

from __future__ import annotations

import glob
from pathlib import Path
from typing import TypedDict

try:
    from langgraph.graph import StateGraph, START, END
    _LANGGRAPH_AVAILABLE = True
except ModuleNotFoundError:
    StateGraph = None  # type: ignore[assignment]
    START = END = None  # type: ignore[assignment]
    _LANGGRAPH_AVAILABLE = False

from careeros.parsing.schema import EvidenceProfile
from careeros.jobs.schema import JobPost
from careeros.matching.service import compute_match, write_match_result
from careeros.ranking.service import rank_all_jobs, write_shortlist
from careeros.ranking.schema import RankedShortlist
from careeros.generation.service import build_package, write_application_package
from careeros.generation.schema import ApplicationPackage
from careeros.guardrails.service import validate_package_against_evidence, write_validation_report


class P21State(TypedDict, total=False):
    run_id: str
    top_n: int
    profile_path: str
    job_path: str
    match_path: str
    shortlist_path: str
    package_path: str
    validation_report_path: str
    validation_status: str
    errors: list[str]


def _latest_file(pattern: str) -> str | None:
    files = glob.glob(pattern)
    if not files:
        return None
    return str(max(files, key=lambda f: Path(f).stat().st_mtime))


def _node_load_context(state: P21State) -> P21State:
    profile_path = state.get("profile_path") or _latest_file("outputs/profile/profile_v1_*.json")
    job_path = state.get("job_path") or _latest_file("outputs/jobs/job_post_v1_*.json")

    if not profile_path or not job_path:
        return {
            "errors": ["Missing profile/job artifacts. Run P2 and P3 first."],
        }

    return {"profile_path": profile_path, "job_path": job_path}


def _node_match(state: P21State) -> P21State:
    profile = EvidenceProfile.model_validate_json(Path(state["profile_path"]).read_text(encoding="utf-8"))
    job = JobPost.model_validate_json(Path(state["job_path"]).read_text(encoding="utf-8"))
    result = compute_match(profile, job, state["run_id"], state["profile_path"], state["job_path"])
    out = write_match_result(result)
    return {"match_path": str(out)}


def _node_rank(state: P21State) -> P21State:
    top_n = int(state.get("top_n", 3))
    shortlist = rank_all_jobs(profile_path=state["profile_path"], top_n=top_n, run_id=state["run_id"])
    out = write_shortlist(shortlist)
    return {"shortlist_path": str(out)}


def _node_generate(state: P21State) -> P21State:
    shortlist = RankedShortlist.model_validate_json(Path(state["shortlist_path"]).read_text(encoding="utf-8"))
    if not shortlist.items:
        return {"errors": ["Shortlist is empty; cannot generate package."]}

    top_item = shortlist.items[0]
    profile = EvidenceProfile.model_validate_json(Path(shortlist.profile_path).read_text(encoding="utf-8"))
    job = JobPost.model_validate_json(Path(top_item.job_path).read_text(encoding="utf-8"))

    pkg: ApplicationPackage = build_package(
        profile=profile,
        job=job,
        run_id=state["run_id"],
        profile_path=shortlist.profile_path,
        job_path=top_item.job_path,
        overlap_skills=top_item.overlap_skills,
    )
    out = write_application_package(pkg)
    return {"package_path": str(out)}


def _route_on_error(state: P21State) -> str:
    errs = state.get("errors") or []
    return "error" if errs else "ok"


def _node_error(state: P21State) -> P21State:
    return {"errors": state.get("errors", ["unknown_error"])}


def _node_guardrails(state: P21State) -> P21State:
    profile = EvidenceProfile.model_validate_json(Path(state["profile_path"]).read_text(encoding="utf-8"))
    pkg = ApplicationPackage.model_validate_json(Path(state["package_path"]).read_text(encoding="utf-8"))

    report = validate_package_against_evidence(
        profile=profile,
        pkg=pkg,
        run_id=state["run_id"],
        package_path=state["package_path"],
    )
    out = write_validation_report(report)
    return {"validation_report_path": str(out), "validation_status": report.status}


def build_p21_graph():
    if not _LANGGRAPH_AVAILABLE:
        raise RuntimeError("langgraph is not installed; graph compile is unavailable")

    graph = StateGraph(P21State)

    graph.add_node("load_context", _node_load_context)
    graph.add_node("match", _node_match)
    graph.add_node("rank", _node_rank)
    graph.add_node("generate", _node_generate)
    graph.add_node("guardrails", _node_guardrails)
    graph.add_node("error", _node_error)

    graph.add_edge(START, "load_context")
    graph.add_conditional_edges("load_context", _route_on_error, {"ok": "match", "error": "error"})
    graph.add_conditional_edges("match", _route_on_error, {"ok": "rank", "error": "error"})
    graph.add_conditional_edges("rank", _route_on_error, {"ok": "generate", "error": "error"})
    graph.add_conditional_edges("generate", _route_on_error, {"ok": "guardrails", "error": "error"})
    graph.add_conditional_edges("guardrails", _route_on_error, {"ok": END, "error": "error"})
    graph.add_edge("error", END)

    return graph.compile()


def run_langgraph_pipeline(
    *,
    run_id: str,
    profile_path: str | None = None,
    job_path: str | None = None,
    top_n: int = 3,
) -> dict:
    """Run P21 pipeline and return final state.

    Uses LangGraph when installed; otherwise falls back to equivalent
    deterministic step execution so local/dev environments can still run tests.
    """

    initial: P21State = {
        "run_id": run_id,
        "profile_path": profile_path or "",
        "job_path": job_path or "",
        "top_n": int(top_n),
    }

    if not _LANGGRAPH_AVAILABLE:
        state: P21State = dict(initial)
        for step in (_node_load_context, _node_match, _node_rank, _node_generate, _node_guardrails):
            state.update(step(state))
            if _route_on_error(state) == "error":
                state.update(_node_error(state))
                break
        return dict(state)

    app = build_p21_graph()
    result = app.invoke(initial)
    return dict(result)
