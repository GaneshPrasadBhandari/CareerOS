import json
from pathlib import Path

from careeros.agentic.state_store import write_state
from careeros.agentic.state import OrchestratorState
from careeros.agentic.p14_orchestrator import run_plan_p6_to_p11


def test_p14_returns_error_when_paths_missing(tmp_path: Path):
    # create a state
    s = OrchestratorState.new()
    write_state(s, out_dir=str(tmp_path))

    out = run_plan_p6_to_p11(
        run_id=s.run_id,
        profile_path=str(tmp_path / "missing_profile.json"),
        job_path=str(tmp_path / "missing_job.json"),
    )
    assert out["status"] == "error"
