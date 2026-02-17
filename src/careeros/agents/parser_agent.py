from __future__ import annotations

from typing import Any

from careeros.phase3.next_steps import parser_extract


def run(payload: dict[str, Any]) -> dict[str, Any]:
    return parser_extract(payload)
