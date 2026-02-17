from __future__ import annotations

from datetime import datetime, timedelta, timezone


def suggest_interview_slots(*, days_ahead: int = 5, slots_per_day: int = 2) -> dict:
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    slots: list[str] = []
    for d in range(days_ahead):
        day = now + timedelta(days=d + 1)
        for h in range(slots_per_day):
            slots.append((day.replace(hour=14 + h * 2)).isoformat())
    return {"status": "ok", "agent": "scheduler", "suggested_slots_utc": slots}
