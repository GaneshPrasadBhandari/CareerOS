from __future__ import annotations

from typing import Any

from careeros.phase3.next_steps import connector_ingest


def run(payload: dict[str, Any]) -> dict[str, Any]:
    return connector_ingest(payload)
