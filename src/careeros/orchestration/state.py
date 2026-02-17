from __future__ import annotations

from typing import TypedDict


class AutomationState(TypedDict, total=False):
    run_id: str
    provider: str
    tier: str
    status: str
    error: str
