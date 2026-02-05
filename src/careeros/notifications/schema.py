from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DraftMessage:
    channel: str  # "email" | "linkedin" | "note"
    subject: Optional[str]
    body: str


@dataclass
class DraftItem:
    draft_id: str
    action_id: str
    application_id: str
    action_type: str
    title: str
    priority: str
    due_at_utc: str
    created_at_utc: str
    messages: List[DraftMessage]


@dataclass
class DraftBundle:
    version: str
    run_id: str
    created_at_utc: str
    source_followups_path: str
    total: int
    items: List[DraftItem]
