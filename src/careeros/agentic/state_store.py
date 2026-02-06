from __future__ import annotations

from pathlib import Path
from careeros.core.settings import load_settings
from .state import OrchestratorState

settings = load_settings()


def write_state(state: OrchestratorState, out_dir: str = "outputs/runs") -> Path:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    fp = Path(out_dir) / f"state_{state.run_id}.json"
    fp.write_text(state.model_dump_json(indent=2), encoding="utf-8")
    return fp
