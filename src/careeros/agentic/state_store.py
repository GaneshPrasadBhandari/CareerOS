from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Union

from careeros.agentic.state import OrchestratorState

PathLike = Union[str, Path]


def _resolve_state_path(path_or_run_id: PathLike, out_dir: str = "outputs/runs") -> Path:
    p = Path(path_or_run_id)
    if p.suffix == ".json":
        return p
    # assume it's a run_id
    return Path(out_dir) / f"state_{str(path_or_run_id)}.json"


def write_state(state: OrchestratorState, out_dir: str = "outputs/runs") -> str:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"state_{state.run_id}.json"
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
    return str(path)


def load_state(path_or_run_id: PathLike, out_dir: str = "outputs/runs") -> OrchestratorState:
    p = _resolve_state_path(path_or_run_id, out_dir=out_dir)
    if not p.exists():
        raise FileNotFoundError(f"State file not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    return OrchestratorState.model_validate(data)


def latest_state_path(out_dir: str = "outputs/runs") -> Optional[str]:
    out = Path(out_dir)
    if not out.exists():
        return None
    files = sorted(out.glob("state_*.json"))
    return str(files[-1]) if files else None
