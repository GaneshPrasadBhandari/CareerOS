from __future__ import annotations

from careeros.phase3.next_steps import write_p22_approval_decision


def run(*, run_id: str, approved: bool, reviewer: str = "human", notes: str | None = None):
    return write_p22_approval_decision(run_id=run_id, approved=approved, reviewer=reviewer, notes=notes)
