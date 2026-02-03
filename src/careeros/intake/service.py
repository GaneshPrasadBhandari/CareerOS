from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

from src.careeros.intake.schema import IntakeBundle


def write_intake_bundle(bundle: IntakeBundle, out_dir: str = "outputs/intake") -> Path:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = Path(out_dir) / f"intake_bundle_{bundle.version}_{ts}.json"
    path.write_text(bundle.model_dump_json(indent=2), encoding="utf-8")
    return path
