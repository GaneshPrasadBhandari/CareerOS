from __future__ import annotations

from careeros.notifications.service import generate_drafts_from_followups


def run(*, followups_path: str, run_id: str | None = None):
    return generate_drafts_from_followups(followups_path, run_id=run_id)
