from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class NextAction:
    action_id: str
    application_id: str
    action_type: str
    title: str
    priority: str
    due_at_utc: str
    created_at_utc: str
    notes: str = ""


@dataclass
class ActionQueue:
    version: str
    run_id: str
    created_at_utc: str
    source_tracking_path: str
    followup_days: int
    stale_days: int
    actions: List[NextAction]

    @property
    def total(self) -> int:
        return len(self.actions)

    # test compatibility: some code expects q.items
    @property
    def items(self) -> List[NextAction]:
        return self.actions
