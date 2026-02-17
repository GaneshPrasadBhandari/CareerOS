from __future__ import annotations

from typing import Protocol


class JobBoardConnector(Protocol):
    def fetch_jobs(self, *, query: str, location: str | None = None, limit: int = 25) -> list[dict]: ...
