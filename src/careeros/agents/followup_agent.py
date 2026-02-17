from __future__ import annotations

from careeros.followups.service import generate_next_actions


def run(*, tracking_path: str, followup_days: int = 3, stale_days: int = 14, run_id: str | None = None):
    return generate_next_actions(tracking_path, followup_days=followup_days, stale_days=stale_days, run_id=run_id)
